import sys
import os

os.environ["QT_MEDIA_BACKEND"] = "ffmpeg"
os.environ["QT_FFMPEG_HWACCEL"] = "none"
# os.environ["QSG_RHI_BACKEND"] = "software"

from PyQt6.QtWidgets import QApplication, QToolTip, QDialog
from PyQt6.QtGui import QFont, QIcon
from ui.browser import ComfyBrowser
from ui.dialogs.setup_window import SetupWindow
from ui.dialogs.build_manager_dialog import BuildManagerDialog
from ui.theme.manager import THEME
from launcher import comfy_exists
from config import get_comfyui_path, ICON_PATH, load_user_config, save_user_config


def launch_app():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(ICON_PATH))
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

    # ── BUILD MANAGER (ВСЕГДА) ─────────────────────────────
    data = load_user_config()
    builds = data.get("builds", []) or []

    # если по какой-то причине builds пустой — уходим в setup
    if not builds:
        setup = SetupWindow()
        result = setup.exec()
        if result != QDialog.DialogCode.Accepted:
            sys.exit(0)
        data = load_user_config()
        builds = data.get("builds", []) or []
        if not builds:
            sys.exit(0)

    mgr = BuildManagerDialog()
    result = mgr.exec()
    if result != QDialog.DialogCode.Accepted or not mgr.selected_build_id:
        sys.exit(0)

    # перечитываем конфиг — пользователь мог добавить новый билд внутри менеджера
    data = load_user_config()
    builds = data.get("builds", []) or []

    # применяем выбор -> записываем comfyui_path и last_used_build_id
    selected = None
    for b in builds:
        if b.get("id") == mgr.selected_build_id:
            selected = b
            break

    if not selected:
        sys.exit(0)

    data["last_used_build_id"] = selected["id"]
    data["comfyui_path"] = selected["path"]
    save_user_config(data)

    # ─── MAIN UI (ВСЕГДА) ────────────────────────────────────
    win = ComfyBrowser()
    app.window = win

    # ─── EVENT LOOP ─────────────────────────────────────────
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_app()
