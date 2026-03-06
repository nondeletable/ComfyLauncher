from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPainterPath, QRegion
from PyQt6.QtCore import Qt, QTimer, QRectF, QThread

import threading
import webbrowser
import os
import time
from datetime import datetime

from ui.header import HeaderBar
from workers.comfy_loader import ComfyLoaderWorker
from ui.settings.settings_window import SettingsWindow
from ui.dialogs.messagebox import MessageBox as MB
from ui.dialogs.console_window import ConsoleWindow
from ui.error_page import ErrorWidget, ErrorScreen
from core.errors import ERRORS
from version import __version__
from ui.splash_video import LauncherSplashVideo
from ui.webview2_widget import WebView2Widget
from utils.logger import log_event
from utils.update_checker import UpdateService
from launcher import (
    ensure_comfyui_running,
    stop_comfyui_hard,
    is_port_open,
)
from config import (
    get_comfyui_path,
    COMFYUI_PORT,
    load_user_config,
    save_user_config,
    SPLASH_PATH,
)


class StartingWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel("🚀 Запуск ComfyUI…")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 18px; color: #cccccc;")

        layout.addWidget(label)


class ComfyBrowser(QMainWindow):
    def __init__(self, poll_callback=None):
        super().__init__()
        self.poll_callback = poll_callback
        self.error_widget = None
        self.setWindowTitle("ComfyLauncher")
        self.comfyui_path = get_comfyui_path()
        self.settings_window = None

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Status check timer
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.check_server_status)  # type: ignore
        self.status_timer.start(3000)

        # header
        self.header = HeaderBar(self)
        self.starting_widget = StartingWidget()

        # central container
        central = QWidget(self)
        central.setObjectName("CentralContainer")
        central.setStyleSheet(
            """
            QWidget#CentralContainer {
                background-color: #353535;
            }
        """
        )
        vbox = QVBoxLayout(central)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        vbox.addWidget(self.header)  # header on top
        vbox.addStretch(1)

        self.setCentralWidget(central)

        self.status_label = self.header.status_label
        QTimer.singleShot(100, lambda: self._round_corners(10))

        # ── Binding signals to methods ───────────────────
        self.header.console_clicked.connect(self.open_console_logs)
        self.header.restart_clicked.connect(self.restart_comfy)
        self.header.stop_clicked.connect(self.stop_comfy)
        self.header.folder_clicked.connect(self.open_folder)
        self.header.settings_clicked.connect(self.open_settings)
        self.header.output_clicked.connect(self.open_output)

        self.ui_state = "STARTING_COMFY"
        self._start_comfyui()

    # ──────────────────────────────────────────────
    def restart_comfy(self):
        """Restart ComfyUI: if running — soft stop, then restart; if stopped — start fresh."""
        if getattr(self, "_restart_in_progress", False):
            log_event("⏳ Restart already in progress — ignored.")
            return

        self._restart_in_progress = True
        log_event("🔄 Restarting ComfyUI...")

        # We block the Restart button so that it cannot be pressed again.
        try:
            self.header.btn_restart.setEnabled(False)
        except Exception:
            pass

        # Status and design
        self.status_label.setText("🟠 Restarting...")
        self.status_label.setStyleSheet("color: orange; font-weight: bold;")

        def do_restart():
            # If the server is running, we soft-stop it.
            if is_port_open(COMFYUI_PORT):
                log_event("🟢 Server detected — performing soft stop.")
                stop_comfyui_hard(self.comfyui_path)
            else:
                log_event("🔴 Server not running — starting fresh.")

            # We wait until the port is definitely free (up to 5 seconds)
            log_event("⏳ Waiting for port to close...")
            for i in range(10):
                if not is_port_open(COMFYUI_PORT):
                    log_event("🟢 Port closed, continuing restart.")
                    break
                time.sleep(0.5)
            else:
                log_event("⚠️ Port still busy after 5 sec, forcing restart anyway.")

            # Let's restart the server
            ensure_comfyui_running(self.comfyui_path)

            # We check when the server will go up (up to 15 seconds)
            log_event("⏳ Waiting for server to respond...")
            for i in range(30):
                time.sleep(0.5)
                if is_port_open(COMFYUI_PORT):
                    log_event("✅ ComfyUI is back online.")
                    break

            else:
                log_event("⚠️ ComfyUI did not respond after restart.")

            # We return the status and unlock the button
            QTimer.singleShot(0, lambda: self.status_label.setText("🟢 Online"))
            QTimer.singleShot(
                0,
                lambda: self.status_label.setStyleSheet(
                    "color: lightgreen; font-weight: bold;"
                ),
            )

            try:
                self.header.btn_restart.setEnabled(True)
            except Exception:
                pass

            self._restart_in_progress = False
            log_event("✅ Restart complete.")

        threading.Thread(target=do_restart, daemon=True).start()

    def stop_comfy(self):
        reply = MB.ask_yes_no(
            self.window(),
            "Stop confirmation",
            "Completely stop ComfyUI and terminate the process?",
        )
        if not reply:
            return

        stop_comfyui_hard(self.comfyui_path)
        self.header.status_label.setText("Offline")
        self.header.status_label.setStyleSheet("color: red; font-weight: bold;")
        log_event("🟥 ComfyUI completely stopped by the user.")

    def open_folder(self):
        os.startfile(self.comfyui_path)

    def open_settings(self):
        log_event("🧩 Opening settings window...")

        try:
            # If you already have it, raise it.
            if self.settings_window is not None:
                try:
                    # если объект уже удалён (WA_DeleteOnClose), тут может быть RuntimeError
                    if self.settings_window.isVisible():
                        self.settings_window.raise_()
                        self.settings_window.activateWindow()
                        log_event("✅ Settings window already open — raised.")
                        return
                except RuntimeError:
                    # "wrapped C/C++ object has been deleted"
                    self.settings_window = None

            # Create an independent window (parent=None)
            self.settings_window = SettingsWindow(None)

            # When the window is actually destroyed, reset the link
            self.settings_window.destroyed.connect(self._on_settings_destroyed)

            self.settings_window.show()
            self.settings_window.raise_()
            self.settings_window.activateWindow()

            log_event("✅ Settings window opened successfully.")

        except Exception as e:
            import traceback

            log_event("❌ Settings window failed to open:")
            traceback.print_exc()
            log_event(f"❌ Exception type: {type(e).__name__}, message: {e}")

    def _on_settings_destroyed(self, *args):
        self.settings_window = None

    def _close_settings_if_open(self):
        if self.settings_window is not None:
            try:
                self.settings_window.close()
            except RuntimeError:
                pass
            self.settings_window = None

    @staticmethod
    def open_output():
        comfy_path = get_comfyui_path()
        if not comfy_path:
            log_event("⚠️ ComfyUI path is not set. Cannot open output folder.")
            return

        output_dir = os.path.join(comfy_path, "output")

        if os.path.exists(output_dir):
            os.startfile(output_dir)
        else:
            log_event(f"⚠️ Output folder not found: {output_dir}")

    def check_server_status(self):
        """Periodically checks if the server is alive."""
        try:
            if getattr(self, "_restart_in_progress", False):
                # Don't touch the status during the restart.
                return

            if is_port_open(COMFYUI_PORT):
                self.status_label.setText("🟢 Online")
                self.status_label.setStyleSheet("color: lightgreen; font-weight: bold;")
            else:
                self.status_label.setText("🔴 Offline")
                self.status_label.setStyleSheet("color: red; font-weight: bold;")
        except Exception as e:
            log_event(f"⚠️ Error in check_server_status: {e}")

    def load_comfy(self):
        """Reserved for future browser loading logic."""
        pass

    def on_load_finished(self, ok):
        if not ok:
            log_event("⚠️ Page not ready yet (server probably still starting).")
        else:
            log_event("✅ Page loaded successfully.")

    def reload_comfy(self):
        self.load_comfy()
        threading.Thread(target=ensure_comfyui_running, daemon=True).start()
        if self.poll_callback:
            QTimer.singleShot(1000, self.poll_callback)

    def closeEvent(self, event):
        print("CLOSE EVENT FIRED")
        """Reaction to closing depending on user settings"""
        # If a duplicate closeEvent fires while we're already processing exit
        if getattr(self, "_exit_in_progress", False):
            log_event("⚠️ Duplicate closeEvent ignored.")
            event.ignore()
            return

        self._exit_in_progress = True  # mark close sequence started

        user_config = load_user_config()
        ask = user_config.get("ask_on_exit", True)
        mode = user_config.get("exit_mode", "always_stop")

        # ─────────────────────────────
        # CASE 1 — Ask on exit (Yes / No / Cancel)
        # ─────────────────────────────
        if ask:
            choice = MB.ask_exit(
                self,
                "Exit",
                "Shut down ComfyUI server?",
            )

            # YES → stop server + exit
            if choice == "yes":
                log_event("🟥 User chose: YES — stopping ComfyUI and exiting.")
                stop_comfyui_hard(self.comfyui_path)
                self._close_settings_if_open()
                save_user_config(user_config)
                event.accept()
                return

            # NO → exit, but keep server running
            elif choice == "no":
                log_event("🟢 User chose: NO — exiting without stopping ComfyUI.")
                self._close_settings_if_open()
                save_user_config(user_config)  # ← важно!
                event.accept()
                return

            # CANCEL → block closing
            else:  # "cancel"
                log_event("ℹ️ User cancelled exit.")
                self._exit_in_progress = False  # allow new future attempts
                event.ignore()
            return

        # ─────────────────────────────
        # CASE 2 — Ask is disabled (auto mode)
        # ─────────────────────────────
        if mode == "always_stop":
            log_event("🟥 Auto mode: always_stop — stopping ComfyUI.")
            stop_comfyui_hard(self.comfyui_path)

        elif mode == "never_stop":
            log_event("🟢 Auto mode: never_stop — leaving ComfyUI running.")

        else:
            log_event(f"⚠️ Unknown exit mode: '{mode}' — defaulting to always_stop.")
            stop_comfyui_hard(self.comfyui_path)

        # Save user config anyway (important!)
        save_user_config(user_config)
        self._close_settings_if_open()

        try:
            if hasattr(self, "browser") and self.browser:
                self.browser.shutdown()
        except Exception:
            pass

        event.accept()

    def open_console_logs(self):
        """Open (or raise) the ComfyUI console log window."""
        try:
            if not hasattr(self, "console_window") or self.console_window is None:
                self.console_window = ConsoleWindow(self)
            self.console_window.show()
            self.console_window.raise_()
            self.console_window.activateWindow()
        except Exception as e:
            log_event(f"⚠️ Failed to open console window: {e}")

    def _round_corners(self, radius: int):
        path = QPainterPath()
        rect = QRectF(self.rect())
        path.addRoundedRect(rect, radius, radius)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # recalculate the mask only if the window is already visible
        if self.isVisible():
            self._round_corners(10)

    def _start_comfyui(self):
        self.ui_state = "STARTING_COMFY"

        # ── SHOW SPLASH ─────────────────────
        cfg = load_user_config()
        if cfg.get("show_splash", True):
            if not hasattr(self, "splash") or self.splash is None:
                self.splash = LauncherSplashVideo(SPLASH_PATH)
                self.splash.show()

        self.thread = QThread()
        self.worker = ComfyLoaderWorker(self.comfyui_path)

        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)  # type: ignore

        self.worker.ready.connect(self._on_comfy_ready)
        self.worker.error.connect(self._on_comfy_error)
        self.worker.timeout.connect(self._on_comfy_timeout)

        self.thread.start()

    def _on_comfy_ready(self):
        self.ui_state = "RUNNING"
        self.showMaximized()
        if hasattr(self, "splash") and self.splash:
            self.splash.finish()
            self.splash = None

        url = f"http://127.0.0.1:{COMFYUI_PORT}"
        self.browser = WebView2Widget(url)
        self.browser.loaded.connect(self.on_load_finished)

        # Replace the preloader with a browser
        central = QWidget(self)
        vbox = QVBoxLayout(central)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        vbox.addWidget(self.header)
        vbox.addWidget(self.browser, 1)

        self.setCentralWidget(central)

        # We carefully complete the worker
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()

        QTimer.singleShot(1500, self.start_update_check)

    def _enter_error_state(self, error_code: str):
        self.ui_state = "ERROR_STARTUP"
        self.showMaximized()
        # close the splash
        if hasattr(self, "splash") and self.splash:
            self.splash.finish()
            self.splash = None

        error = ERRORS[error_code]

        error_widget = ErrorWidget(
            title=error.title,
            message=error.message,
            hint=error.hint,
        )

        error_screen = ErrorScreen(error_widget)

        central = QWidget(self)
        central.setObjectName("CentralContainer")
        central.setStyleSheet(
            """
            QWidget#CentralContainer {
                background-color: #353535;
            }
        """
        )

        vbox = QVBoxLayout(central)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        vbox.addWidget(self.header)
        vbox.addWidget(error_screen, 1)

        self.setCentralWidget(central)

        # We carefully stop the worker.
        if hasattr(self, "worker"):
            self.worker.stop()
        if hasattr(self, "thread"):
            self.thread.quit()
            self.thread.wait()

    def _on_comfy_error(self, message: str):
        self._enter_error_state("PROCESS_START_FAILED")

    def _on_comfy_timeout(self):
        self._enter_error_state("COMFY_START_TIMEOUT")

    def cleanup_update_thread(self):
        self.update_thread.quit()
        self.update_thread.wait()
        self.update_service.deleteLater()
        self.update_thread.deleteLater()

    def start_update_check(self):
        self.update_thread = QThread()
        self.update_service = UpdateService("nondeletable", "ComfyLauncher")

        self.update_service.moveToThread(self.update_thread)

        # когда поток стартует — выполняем проверку
        self.update_thread.started.connect(self.update_service.check_for_updates)  # type: ignore

        # сигналы результата
        self.update_service.update_available.connect(self.on_update_available)
        self.update_service.update_not_found.connect(self.on_update_not_found)
        self.update_service.error_occurred.connect(self.on_update_error)

        # аккуратное завершение
        self.update_service.update_available.connect(self.cleanup_update_thread)
        self.update_service.update_not_found.connect(self.cleanup_update_thread)
        self.update_service.error_occurred.connect(self.cleanup_update_thread)

        self.update_thread.start()

    def on_update_available(self, latest_version, release_url):
        title = "Update available"

        message = (
            f"A new version ({latest_version}) is available.\n\n"
            f"Current version: {__version__}\n\n"
            "Would you like to update now?"
        )

        user_wants_update = MB.update_available(self.window(), title, message)

        if user_wants_update:
            webbrowser.open(release_url)
        else:
            config = load_user_config()
            config["last_update_check"] = datetime.utcnow().isoformat()
            save_user_config(config)

    def on_update_not_found(self):
        print("No updates found")

    def on_update_error(self, error):
        log_event(f"⚠️ Update check error: {error}")
