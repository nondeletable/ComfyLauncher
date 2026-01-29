from __future__ import annotations
import os
from pathlib import Path

os.environ["PYTHONNET_RUNTIME"] = "netfx"

import pythonnet

pythonnet.load("netfx")  # noqa: E402

import clr  # type: ignore  # noqa: E402

from PyQt6.QtCore import pyqtSignal, Qt, QTimer  # noqa: E402
from PyQt6.QtWidgets import QWidget, QVBoxLayout  # noqa: E402


def _wv2_userdata_dir(app_name: str = "ComfyLauncher") -> str:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    p = Path(base) / app_name / "webview2"
    p.mkdir(parents=True, exist_ok=True)
    return str(p)


class WebView2Widget(QWidget):
    loaded = pyqtSignal(bool)

    def __init__(
        self, url: str, dll_dir: str | None = None, parent: QWidget | None = None
    ):
        super().__init__(parent)
        self._url = url
        self._core_ready = False

        # Container with HWND WebView2
        self._host = QWidget(self)
        self._host.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        self._host.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors, True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._host, 1)

        self._webview = None
        self._panel_hwnd = None

        self._init_webview2(dll_dir=dll_dir)

        # pump для WinForms (иначе WebView2 часто не инициализируется/не рисуется)
        self._pump = QTimer(self)
        self._pump.setInterval(10)
        self._pump.timeout.connect(self._do_events)
        self._pump.start()

        # запускаем инициализацию WebView2 уже ПОСЛЕ того, как Qt начнет показывать окно
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
                "Не найдены DLL WebView2 в папке:\n"
                f"{base}\n"
                "Нужны: Microsoft.Web.WebView2.WinForms.dll, Microsoft.Web.WebView2.Core.dll, WebView2Loader.dll"
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

            web.CreationProperties = props
            print(f"[WV2] UserDataFolder = {user_data}")
        except Exception as e:
            print(f"[WV2] Failed to set UserDataFolder: {e}")

        web.Dock = DockStyle.Fill

        panel.Controls.Add(web)

        # create hendlers
        panel.CreateControl()
        web.CreateControl()

        self._webview = web
        self._panel_hwnd = int(panel.Handle.ToInt64())

        # флаг: ещё НЕ встроили в Qt
        self._embedded = False

    def showEvent(self, event):
        super().showEvent(event)

        # showEvent может вызываться несколько раз — встраиваем только один раз
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
        dpr = 1.0
        try:
            wh = self.window().windowHandle()
            if wh:
                dpr = float(wh.devicePixelRatio())
        except Exception:
            dpr = 1.0

        w = max(1, int(rect.width() * dpr))
        h = max(1, int(rect.height() * dpr))

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
                self.loaded.emit(True)
        except Exception:
            self.loaded.emit(False)

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
        Аккуратное освобождение. Не идеально, но снижает шанс краша при выходе.
        """
        try:
            if getattr(self, "_pump", None):
                self._pump.stop()
        except Exception:
            pass

        try:
            if self._webview is not None:
                self._webview.Dispose()
        except Exception:
            pass
        self._webview = None

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
                    # грузим URL только когда Core готов
                    self.navigate(self._url)
                self.loaded.emit(ok)

            self._webview.CoreWebView2InitializationCompleted += _on_init
            self._webview.EnsureCoreWebView2Async(None)  # ВАЖНО: без ожидания!
        except Exception:
            self.loaded.emit(False)
