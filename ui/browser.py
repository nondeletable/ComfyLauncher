from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtGui import QIcon, QPainterPath, QRegion
from PyQt6.QtCore import Qt, QTimer, QUrl, QRectF

import threading
import os
import time

from config import ICON_PATH, get_comfyui_path, COMFYUI_PORT, load_user_config, save_user_config
from ui.header import HeaderBar
from ui.error_page import ErrorPage
from ui.settings.settings_window import SettingsWindow
from ui.dialogs.messagebox import MessageBox as MB
from ui.dialogs.console_window import ConsoleWindow
from launcher import (
    ensure_comfyui_running,
    stop_comfyui_hard,
    is_port_open,
)


class ComfyBrowser(QMainWindow):
    def __init__(self, poll_callback=None):
        super().__init__()
        self.poll_callback = poll_callback
        self.error_widget = None
        self.setWindowTitle("ComfyLauncher")
        self.setWindowIcon(QIcon(ICON_PATH))
        self.comfyui_path = get_comfyui_path()

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # The central widget is a built-in browser.
        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)
        self.browser.loadFinished.connect(self.on_load_finished)
        self.load_comfy()

        # Status check timer
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.check_server_status)  # type: ignore
        self.status_timer.start(3000)

        # header
        self.header = HeaderBar(self)

        # central container
        central = QWidget(self)
        vbox = QVBoxLayout(central)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        vbox.addWidget(self.header)  # header on top
        vbox.addWidget(self.browser)

        self.setCentralWidget(central)
        self.status_label = self.header.status_label
        self.showMaximized()
        QTimer.singleShot(100, lambda: self._round_corners(10))

        # ── Binding signals to methods ───────────────────
        self.header.console_clicked.connect(self.open_console_logs)
        self.header.restart_clicked.connect(self.restart_comfy)
        self.header.stop_clicked.connect(self.stop_comfy)
        self.header.folder_clicked.connect(self.open_folder)
        self.header.settings_clicked.connect(self.open_settings)
        self.header.output_clicked.connect(self.open_output)

    # ──────────────────────────────────────────────
    def restart_comfy(self):
        """Restart ComfyUI: if running — soft stop, then restart; if stopped — start fresh."""
        if getattr(self, "_restart_in_progress", False):
            print("⏳ Restart already in progress — ignored.")
            return

        self._restart_in_progress = True
        print("🔄 Restarting ComfyUI...")

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
                print("🟢 Server detected — performing soft stop.")
                stop_comfyui_hard()
            else:
                print("🔴 Server not running — starting fresh.")

            # We wait until the port is definitely free (up to 5 seconds)
            print("⏳ Waiting for port to close...")
            for i in range(10):
                if not is_port_open(COMFYUI_PORT):
                    print("🟢 Port closed, continuing restart.")
                    break
                time.sleep(0.5)
            else:
                print("⚠️ Port still busy after 5 sec, forcing restart anyway.")

            # Let's restart the server
            ensure_comfyui_running(self.comfyui_path)

            # We check when the server will go up (up to 15 seconds)
            print("⏳ Waiting for server to respond...")
            for i in range(30):
                time.sleep(0.5)
                if is_port_open(COMFYUI_PORT):
                    print("✅ ComfyUI is back online.")
                    break

            else:
                print("⚠️ ComfyUI did not respond after restart.")

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
            print("✅ Restart complete.")

        threading.Thread(target=do_restart, daemon=True).start()

    def stop_comfy(self):
        reply = MB.ask_yes_no(
            self,
            "Stop confirmation",
            "Completely stop ComfyUI and terminate the process?",
        )
        if not reply:
            return

        stop_comfyui_hard()
        self.header.status_label.setText("Offline")
        self.header.status_label.setStyleSheet("color: red; font-weight: bold;")
        print("🟥 ComfyUI completely stopped by the user.")

    def open_folder(self):
        os.startfile(self.comfyui_path)

    def open_settings(self):
        print("🧩 Opening settings window...")
        try:
            self.settings_window = SettingsWindow(None)
            self.settings_window.show()
            print("✅ Settings window opened successfully.")
        except Exception as e:
            import traceback

            print("❌ Settings window failed to open:")
            traceback.print_exc()
            print(f"❌ Exception type: {type(e).__name__}, message: {e}")

    @staticmethod
    def open_output():
        comfy_path = get_comfyui_path()
        if not comfy_path:
            print("⚠️ ComfyUI path is not set. Cannot open output folder.")
            return

        output_dir = os.path.join(comfy_path, "output")

        if os.path.exists(output_dir):
            os.startfile(output_dir)
        else:
            print(f"⚠️ Output folder not found: {output_dir}")

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
            print(f"⚠️ Error in check_server_status: {e}")

    def load_comfy(self):
        url = QUrl(f"http://127.0.0.1:{COMFYUI_PORT}")
        self.browser.load(url)

    def on_load_finished(self, ok):
        """Handler for successful/failed page loading."""
        if not ok:
            # If there is a restart, do not show the error_page
            if getattr(self, "_restart_in_progress", False):
                print("⏳ Restart in progress — skipping error page.")
                return

            print("⚠️ Error loading page — showing error page.")
            self.show_error_page()
        else:
            print("✅ Page loaded successfully.")

    def show_error_page(self):
        self.error_widget = ErrorPage(self.reload_comfy)
        self.setCentralWidget(self.error_widget)

    def reload_comfy(self):
        self.setCentralWidget(self.browser)
        self.load_comfy()
        threading.Thread(target=ensure_comfyui_running, daemon=True).start()
        if self.poll_callback:
            QTimer.singleShot(1000, self.poll_callback)

    def closeEvent(self, event):
        """Reaction to closing depending on user settings"""

        # If a duplicate closeEvent fires while we're already processing exit
        if getattr(self, "_exit_in_progress", False):
            print("⚠️ Duplicate closeEvent ignored.")
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
                print("🟥 User chose: YES — stopping ComfyUI and exiting.")
                stop_comfyui_hard()

                save_user_config(user_config)  # ← важно!
                event.accept()
                return

            # NO → exit, but keep server running
            elif choice == "no":
                print("🟢 User chose: NO — exiting without stopping ComfyUI.")

                save_user_config(user_config)  # ← важно!
                event.accept()
                return

            # CANCEL → block closing
            else:  # "cancel"
                print("ℹ️ User cancelled exit.")
                self._exit_in_progress = False  # allow new future attempts
                event.ignore()
            return

        # ─────────────────────────────
        # CASE 2 — Ask is disabled (auto mode)
        # ─────────────────────────────
        if mode == "always_stop":
            print("🟥 Auto mode: always_stop — stopping ComfyUI.")
            stop_comfyui_hard()

        elif mode == "never_stop":
            print("🟢 Auto mode: never_stop — leaving ComfyUI running.")

        else:
            print(f"⚠️ Unknown exit mode: '{mode}' — defaulting to always_stop.")
            stop_comfyui_hard()

        # Save user config anyway (important!)
        save_user_config(user_config)

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
            print(f"⚠️ Failed to open console window: {e}")

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
