import sys
import os

os.environ["QSG_RHI_BACKEND"] = "software"

from PyQt6.QtWidgets import QApplication, QToolTip, QDialog
from PyQt6.QtCore import QThread
from PyQt6.QtGui import QFont

from workers.comfy_loader import ComfyLoaderWorker
from ui.splash_video import LauncherSplashVideo
from ui.browser import ComfyBrowser
from ui.dialogs.setup_window import SetupWindow
from ui.theme.manager import THEME
from ui.dialogs.messagebox import MessageBox as MB
from utils.logger import log_event
from launcher import comfy_exists
from config import SPLASH_PATH, get_comfyui_path


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
    first_launch = False

    # ---------- FIRST SETUP ----------
    if not comfy_path or not comfy_exists(comfy_path):
        first_launch = True
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

    # ---------- VALIDATE AGAIN ----------
    if not comfy_path or not comfy_exists(comfy_path):
        log_event(f"❌ ComfyUI not found even after setup: {comfy_path}")
        MB.error(
            None,
            "Ошибка",
            f"ComfyUI не найден по пути:\n{comfy_path}\n\n"
            "Укажите правильную папку в настройках.",
        )
        return sys.exit(1)


    # ---------- SHOW SPLASH ----------
    log_event("💫 Splash screen shown. Launching ComfyUI server...")
    splash = LauncherSplashVideo(
        video_path=SPLASH_PATH,
    )
    splash.show()

    # ---------- START WORKER ----------
    thread = QThread()
    worker = ComfyLoaderWorker(
        comfy_path=comfy_path,
        first_launch=first_launch,
    )
    worker.moveToThread(thread)

    thread.started.connect(worker.run)

    def on_ready():
        splash.finish()
        win = ComfyBrowser()
        app.window = win
        win.show()

        worker.stop()
        thread.quit()
        thread.wait()

    def on_timeout():
        splash.finish()
        win = ComfyBrowser()
        app.window = win
        win.show_error_page()

        worker.stop()
        thread.quit()
        thread.wait()

    def on_error(msg):
        log_event(f"❌ Worker error: {msg}")
        splash.finish()
        win = ComfyBrowser()
        app.window = win
        win.show_error_page()

        worker.stop()
        thread.quit()
        thread.wait()

    worker.ready.connect(on_ready)
    worker.timeout.connect(on_timeout)
    worker.error.connect(on_error)

    thread.start()

    log_event("✨ Qt event loop started.")
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_app()
