import sys
import threading
import time

from PyQt6.QtWidgets import QApplication, QToolTip, QDialog
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFont

from ui.splash import AnimatedSplash
from ui.browser import ComfyBrowser
from ui.dialogs.setup_window import SetupWindow
from ui.theme.manager import THEME
from ui.dialogs.messagebox import MessageBox as MB
from utils.logger import log_event
from launcher import comfy_exists, ensure_comfyui_running, is_port_open
from config import SPLASH_PATH, COMFYUI_PORT, MAX_WAIT_TIME, get_comfyui_path


def launch_app():
    app = QApplication(sys.argv)
    THEME.apply()

    QToolTip.setFont(QFont("Segoe UI", 9))
    app.setStyleSheet(
        """
        QToolTip {
            background-color: #2b2b2b;
            color: white;
            padding: 3px 6px;
            border-radius: 4px;
        }
    """
    )
    comfy_path = get_comfyui_path()

    if not comfy_exists(comfy_path):
        log_event(
            "🆕 [FIRST SETUP] ComfyUI not found or invalid — opening Setup Dialog."
        )
        setup = SetupWindow()
        if setup.exec() != QDialog.DialogCode.Accepted:
            log_event("🟥 [FIRST SETUP] Setup canceled — showing ErrorPage fallback.")
            app.window = ComfyBrowser()
            app.window.show_error_page()
            return sys.exit(app.exec())

        comfy_path = get_comfyui_path()
        log_event(f"✅ [FIRST SETUP] User selected path: {comfy_path}")

    if not comfy_exists(comfy_path):
        log_event(f"❌ ComfyUI not found even after setup: {comfy_path}")
        MB.error(
            None,
            "Ошибка",
            f"ComfyUI не найден по пути:\n{comfy_path}\n\n"
            "Укажите правильную папку в настройках.",
        )
        return sys.exit(1)

    log_event("💫 Splash screen shown. Launching ComfyUI server...")
    splash = AnimatedSplash(SPLASH_PATH, "Launching ComfyUI...")
    splash.show()

    def open_browser(error=False):
        splash.finish(None)
        win = ComfyBrowser(poll_callback=poll_ready)
        app.window = win
        if error:
            log_event("🟥 Timeout reached — showing ErrorPage in browser.")
            win.show_error_page()
        else:
            log_event("🟢 Browser opened successfully.")
            win.show()

    def poll_ready(start=time.time()):
        elapsed = int(time.time() - start)
        splash.update_message(elapsed, MAX_WAIT_TIME)
        if is_port_open(COMFYUI_PORT):
            log_event(f"✅ ComfyUI server responded on port {COMFYUI_PORT}.")
            return open_browser()
        if elapsed > MAX_WAIT_TIME:
            log_event("⏰ Timeout: ComfyUI server did not respond in time.")
            return open_browser(error=True)
        QTimer.singleShot(500, lambda: poll_ready(start))

    threading.Thread(
        target=ensure_comfyui_running, args=(get_comfyui_path(),), daemon=True
    ).start()
    log_event("🧠 Background thread started: ensure_comfyui_running()")
    poll_ready()

    log_event("🪄 Qt event loop started.")
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_app()
