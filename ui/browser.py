from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PyQt6.QtGui import QIcon, QPainterPath, QRegion
from PyQt6.QtCore import Qt, QTimer, QUrl, QRectF

import threading
import os
import time

from ui.header import HeaderBar
from launcher import (
    ensure_comfyui_running,
    stop_comfyui_hard,
    is_port_open,
)
from config import ICON_PATH, get_comfyui_path, COMFYUI_PORT, load_user_config
from ui.error_page import ErrorPage
from ui.settings.settings_window import SettingsWindow
from ui.dialogs.messagebox import MessageBox as MB
from config import COMFYUI_PATH


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

        # 🔒 Блокируем кнопку Restart, чтобы не нажали снова
        try:
            self.header.btn_restart.setEnabled(False)
        except Exception:
            pass

        # 🔶 Статус и оформление
        self.status_label.setText("🟠 Restarting...")
        self.status_label.setStyleSheet("color: orange; font-weight: bold;")

        def do_restart():
            # 1️⃣ Если сервер запущен — мягко останавливаем
            if is_port_open(COMFYUI_PORT):
                print("🟢 Server detected — performing soft stop.")
                stop_comfyui_hard()
            else:
                print("🔴 Server not running — starting fresh.")

            # 2️⃣ Ждём, пока порт точно освободится (до 5 сек)
            print("⏳ Waiting for port to close...")
            for i in range(10):
                if not is_port_open(COMFYUI_PORT):
                    print("🟢 Port closed, continuing restart.")
                    break
                time.sleep(0.5)
            else:
                print("⚠️ Port still busy after 5 sec, forcing restart anyway.")

            # 3️⃣ Запускаем сервер заново
            ensure_comfyui_running(self.comfyui_path)

            # 4️⃣ Проверяем, когда сервер поднимется (до 15 сек)
            print("⏳ Waiting for server to respond...")
            for i in range(30):
                time.sleep(0.5)
                if is_port_open(COMFYUI_PORT):
                    print("✅ ComfyUI is back online.")
                    break

            else:
                print("⚠️ ComfyUI did not respond after restart.")

            # 5️⃣ Возвращаем статус и разблокируем кнопку
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
        output_dir = os.path.join(COMFYUI_PATH, "output")
        if os.path.exists(output_dir):
            os.startfile(output_dir)
        else:
            print(f"⚠️ Output folder not found: {output_dir}")

    def check_server_status(self):
        """Периодически проверяет, жив ли сервер."""
        try:
            if getattr(self, "_restart_in_progress", False):
                # 🔄 во время рестарта не трогаем статус
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
        """Обработчик успешной/неудачной загрузки страницы."""
        if not ok:
            # 🚫 Если идёт рестарт — не показываем error_page
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
        user_config = load_user_config()
        ask = user_config.get("ask_on_exit", True)
        mode = user_config.get("exit_mode", "always_stop")

        if ask:
            reply = MB.ask_yes_no(
                self,
                "Completion of work",
                "Shut down ComfyUI server?",
            )
            if reply:
                stop_comfyui_hard()
                print("🟥 The server was stopped by the user on exit.")
            else:
                print("🟢 The server continues to run in the background.")
            event.accept()
            return

        # If Ask is disabled
        if mode == "always_stop":
            stop_comfyui_hard()
            print("🟥 Auto-stop ComfyUI (always_stop mode).")
        elif mode == "never_stop":
            print("🟢 Auto-keep ComfyUI running (never_stop mode).")

        event.accept()

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
