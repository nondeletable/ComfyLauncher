import sys
import os

os.environ["QT_MEDIA_BACKEND"] = "ffmpeg"
os.environ["QT_FFMPEG_HWACCEL"] = "none"
os.environ["QSG_RHI_BACKEND"] = "software"

from PyQt6.QtWidgets import QApplication, QToolTip, QDialog
from PyQt6.QtGui import QFont
from ui.browser import ComfyBrowser
from ui.dialogs.setup_window import SetupWindow
from ui.theme.manager import THEME
from launcher import comfy_exists
from config import get_comfyui_path


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

    # ── FIRST SETUP ─────────────────────────────
    comfy_path = get_comfyui_path()
    if not comfy_path or not comfy_exists(comfy_path):
        setup = SetupWindow()
        result = setup.exec()

        # Cancel / крестик -> это выход из программы
        if result != QDialog.DialogCode.Accepted:
            sys.exit(0)

        # пользователь мог выбрать путь — перечитываем заново
        comfy_path = get_comfyui_path()
        if not comfy_path or not comfy_exists(comfy_path):
            # на всякий случай: если окно закрылось "ОК", но путь так и не появился
            sys.exit(0)

    # ─── MAIN UI (ВСЕГДА) ────────────────────────────────────
    win = ComfyBrowser()
    app.window = win
    # win.show()

    # ─── EVENT LOOP ─────────────────────────────────────────
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_app()
