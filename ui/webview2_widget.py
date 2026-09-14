from __future__ import annotations
import os
from pathlib import Path

os.environ["PYTHONNET_RUNTIME"] = "netfx"

import pythonnet

pythonnet.load("netfx")  # noqa: E402

import clr  # type: ignore  # noqa: E402

from PyQt6.QtCore import (  # noqa: E402
    pyqtSignal,
    Qt,
    QTimer,
    QPropertyAnimation,
    QPoint,
)
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel  # noqa: E402

from ui.theme.manager import THEME  # noqa: E402


class _DownloadToast(QWidget):
    """Frameless top-level toast shown after a silent download.

    It is a separate always-on-top window (not a child widget) on purpose:
    the WebView2 panel is a native HWND reparented into Qt, and native
    windows paint on top of Qt children — a plain child QLabel would be
    hidden behind the web view. A top-level window renders above it.
    """

    _AUTOHIDE_MS = 2500

    def __init__(self):
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowDoesNotAcceptFocus,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self._label = QLabel(self)
        self._label.setTextFormat(Qt.TextFormat.RichText)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._start_fade)  # type: ignore

        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setDuration(300)
        self._fade.setStartValue(1.0)
        self._fade.setEndValue(0.0)
        self._fade.finished.connect(self.hide)  # type: ignore

    def _restyle(self):
        c = THEME.colors
        self._label.setStyleSheet(
            f"""
            QLabel {{
                background-color: {c['popup_bg']};
                color: {c['popup_text']};
                border: 1px solid {c['popup_border']};
                border-radius: 8px;
                padding: 9px 14px;
                font-size: 13px;
            }}
            """
        )

    def show_saved(self, name: str, full_path: str, anchor: QWidget):
        """Show '✔ Saved: <name>' anchored to the bottom-center of ``anchor``."""
        self._restyle()
        c = THEME.colors
        safe = name.replace("<", "&lt;").replace(">", "&gt;")
        self._label.setText(
            f'<span style="color:{c["success"]};font-weight:bold;">✔</span>'
            f"&nbsp;&nbsp;Сохранено: "
            f'<span style="color:{c["text_secondary"]};">{safe}</span>'
        )
        self._label.setToolTip(full_path)

        self._fade.stop()
        self.setWindowOpacity(1.0)
        self.adjustSize()

        rect = anchor.rect()
        bottom_center = anchor.mapToGlobal(
            QPoint(rect.width() // 2, rect.height() - 16 - self.height())
        )
        self.move(bottom_center.x() - self.width() // 2, bottom_center.y())

        self.show()
        self.raise_()
        self._hide_timer.start(self._AUTOHIDE_MS)

    def _start_fade(self):
        self._fade.stop()
        self._fade.start()


def _wv2_userdata_dir(app_name: str = "ComfyLauncher") -> str:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    p = Path(base) / app_name / "webview2"
    p.mkdir(parents=True, exist_ok=True)
    return str(p)


class WebView2Widget(QWidget):
    loaded = pyqtSignal(bool)
    # (basename, full_path) — emitted from the WebView2 event when a download finishes
    download_saved = pyqtSignal(str, str)

    def __init__(
        self, url: str, dll_dir: str | None = None, parent: QWidget | None = None
    ):
        super().__init__(parent)
        self._url = url
        self._core_ready = False

        # The container where we will "paste" the WebView2 HWND
        self._host = QWidget(self)
        self._host.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        self._host.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._host, 1)

        self._webview = None
        self._panel_hwnd = None

        # Silent-download toast (created lazily on first download)
        self._toast: _DownloadToast | None = None
        self.download_saved.connect(self._show_download_toast)

        self._init_webview2(dll_dir=dll_dir)

        # pump for WinForms (otherwise WebView2 often doesn't initialize/draw)
        self._pump = QTimer(self)
        self._pump.setInterval(10)
        self._pump.timeout.connect(self._do_events)  # type: ignore
        self._pump.start()

        # We start the initialization of WebView2 AFTER Qt starts showing the window
        QTimer.singleShot(200, self._ensure_core_async)

    def _init_webview2(self, dll_dir: str | None):
        import ctypes
        from pathlib import Path

        # 1) Folder with DLL
        base = Path(dll_dir) if dll_dir else (Path(__file__).parent / "webview2_dll")

        winforms_dll = base / "Microsoft.Web.WebView2.WinForms.dll"
        core_dll = base / "Microsoft.Web.WebView2.Core.dll"
        loader_dll = base / "WebView2Loader.dll"

        if not (winforms_dll.exists() and core_dll.exists() and loader_dll.exists()):
            raise RuntimeError(
                "WebView2 DLLs were not found in folder:\n"
                f"{base}\n"
                "Required: Microsoft.Web.WebView2.WinForms.dll, Microsoft.Web.WebView2.Core.dll, WebView2Loader.dll"
            )

        # важно: чтобы native loader точно находился
        os.add_dll_directory(str(base))
        ctypes.WinDLL(str(loader_dll))

        # 2) CLR refs

        clr.AddReference(str(winforms_dll))  # type: ignore[attr-defined]
        clr.AddReference(str(core_dll))  # type: ignore[attr-defined]
        clr.AddReference("System.Windows.Forms")  # type: ignore[attr-defined]

        from System.Windows.Forms import Panel, DockStyle, Application  # type: ignore
        from Microsoft.Web.WebView2.WinForms import WebView2  # type: ignore

        self._wf_app = Application

        # 3) WinForms container and WebView2
        panel = Panel()
        self._panel = panel

        panel.Dock = DockStyle.Fill

        web = WebView2()
        try:
            from Microsoft.Web.WebView2.WinForms import CoreWebView2CreationProperties  # type: ignore
            from pathlib import Path

            base = os.environ.get("LOCALAPPDATA") or str(
                Path.home() / "AppData" / "Local"
            )
            user_data = str(Path(base) / "ComfyLauncher" / "webview2")
            Path(user_data).mkdir(parents=True, exist_ok=True)

            props = CoreWebView2CreationProperties()
            props.UserDataFolder = user_data

            # IMPORTANT: For Win10/driver glitches, you can try disabling the GPU.
            # (if the screen is still white after the fix)
            # props.AdditionalBrowserArguments = "--disable-gpu --disable-gpu-compositing"

            web.CreationProperties = props
            print(f"[WV2] UserDataFolder = {user_data}")
        except Exception as e:
            print(f"[WV2] Failed to set UserDataFolder: {e}")

        web.Dock = DockStyle.Fill

        panel.Controls.Add(web)

        # create handles
        panel.CreateControl()
        web.CreateControl()

        self._webview = web
        self._panel_hwnd = int(panel.Handle.ToInt64())

        # flag: NOT yet built into Qt
        self._embedded = False

    def showEvent(self, event):
        super().showEvent(event)

        # showEvent can be called multiple times - we embed it only once
        if getattr(self, "_embedded", False):
            return

        if not getattr(self, "_panel_hwnd", None):
            return

        try:
            import win32gui
            import win32con

            self._host.winId()
            host_hwnd = int(self._host.winId())

            win32gui.SetParent(self._panel_hwnd, host_hwnd)

            style = win32gui.GetWindowLong(self._panel_hwnd, win32con.GWL_STYLE)
            style |= (
                win32con.WS_CHILD | win32con.WS_CLIPSIBLINGS | win32con.WS_CLIPCHILDREN
            )
            win32gui.SetWindowLong(self._panel_hwnd, win32con.GWL_STYLE, style)

            self._embedded = True
            self._resize_native()

        except Exception:
            self._embedded = False

    def _resize_native(self):
        import win32gui

        if not self._panel_hwnd:
            return

        rect = self._host.rect()

        # Qt gives dimensions in logical pixels, but WinAPI wants physical ones
        dpr = 1.0
        try:
            wh = self.window().windowHandle()
            if wh:
                dpr = float(wh.devicePixelRatio())
        except Exception:
            dpr = 1.0

        w = max(1, int(rect.width() * dpr))
        h = max(1, int(rect.height() * dpr))

        # The embedded hwnd is always at (0,0) inside host
        win32gui.MoveWindow(self._panel_hwnd, 0, 0, w, h, True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_native()

    # ── API (минимум браузера) ──────────────────────────────
    def navigate(self, url: str):
        self._url = url
        if not self._core_ready:
            return
        try:
            if self._webview and self._webview.CoreWebView2 is not None:
                self._webview.CoreWebView2.Navigate(url)
                self.loaded.emit(True)  # type: ignore
        except Exception:
            self.loaded.emit(False)  # type: ignore

    def reload(self):
        try:
            if self._webview and self._webview.CoreWebView2:
                self._webview.CoreWebView2.Reload()
        except Exception:
            pass

    def go_back(self):
        try:
            if (
                self._webview
                and self._webview.CoreWebView2
                and self._webview.CoreWebView2.CanGoBack
            ):
                self._webview.CoreWebView2.GoBack()
        except Exception:
            pass

    def go_forward(self):
        try:
            if (
                self._webview
                and self._webview.CoreWebView2
                and self._webview.CoreWebView2.CanGoForward
            ):
                self._webview.CoreWebView2.GoForward()
        except Exception:
            pass

    def shutdown(self):
        """
        Gentle release. Not perfect, but reduces the chance of a crash when exiting.
        """
        try:
            if getattr(self, "_pump", None):
                self._pump.stop()
        except Exception:
            pass

        try:
            if self._toast is not None:
                self._toast.close()
                self._toast = None
        except Exception:
            pass

        try:
            if self._webview is not None:
                self._webview.Dispose()
        except Exception:
            pass
        self._webview = None

    # ── Downloads (silent, no default WebView2 flyout) ──────────
    def _on_download_starting(self, sender, args):
        """Suppress Edge's default download flyout (it covers ComfyUI's RUN
        button) and let the file save silently to the default folder.
        A lightweight in-app toast is shown once the download completes."""
        try:
            # Hide the built-in download UI; the download itself still runs.
            args.Handled = True

            op = args.DownloadOperation

            def _on_state_changed(s, e):
                try:
                    from Microsoft.Web.WebView2.Core import (  # type: ignore
                        CoreWebView2DownloadState,
                    )

                    if op.State == CoreWebView2DownloadState.Completed:
                        path = str(op.ResultFilePath or "")
                        name = os.path.basename(path) if path else "файл"
                        self.download_saved.emit(name, path)  # type: ignore
                except Exception:
                    pass

            op.StateChanged += _on_state_changed
        except Exception:
            pass

    def _show_download_toast(self, name: str, full_path: str):
        if self._toast is None:
            self._toast = _DownloadToast()
        self._toast.show_saved(name, full_path, self)

    def _do_events(self):
        try:
            if getattr(self, "_wf_app", None):
                self._wf_app.DoEvents()
        except Exception:
            pass

    def _ensure_core_async(self):
        if self._webview is None:
            return

        try:
            # событие, когда CoreWebView2 готов
            def _on_init(sender, args):
                ok = bool(args.IsSuccess)
                self._core_ready = ok
                if ok:

                    def _on_nav_completed(sender, args):
                        self.loaded.emit(args.IsSuccess)  # type: ignore

                    self._webview.CoreWebView2.NavigationCompleted += _on_nav_completed
                    self._webview.CoreWebView2.DownloadStarting += (
                        self._on_download_starting
                    )
                    self.navigate(self._url)
                self.loaded.emit(ok)  # type: ignore

            self._webview.CoreWebView2InitializationCompleted += _on_init
            self._webview.EnsureCoreWebView2Async(None)
        except Exception:
            self.loaded.emit(False)  # type: ignore
