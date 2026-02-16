import requests
from datetime import datetime, timedelta
from PyQt6.QtCore import QObject, pyqtSignal
from packaging import version

from version import __version__
from config import load_user_config, save_user_config


class UpdateService(QObject):
    update_available = pyqtSignal(str, str)
    update_not_found = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, repo_owner: str, repo_name: str):
        super().__init__()
        self.repo_owner = repo_owner
        self.repo_name = repo_name

    def check_for_updates(self):
        config = load_user_config()

        # 1️⃣ Проверка включена ли система обновлений
        if not config.get("updates_enabled", True):
            self.update_not_found.emit()  # type: ignore
            return

        # 2️⃣ Проверка интервала
        last_check = config.get("last_update_check")
        interval_hours = config.get("update_interval_hours", 48)

        if last_check:
            try:
                last_dt = datetime.fromisoformat(last_check)
                if datetime.utcnow() - last_dt < timedelta(hours=interval_hours):
                    self.update_not_found.emit()  # type: ignore
                    return
            except Exception:
                pass  # если дата повреждена — просто продолжаем

        try:
            # 3️⃣ Подготовка заголовков (ETag)
            headers = {}
            if config.get("update_etag"):
                headers["If-None-Match"] = config["update_etag"]

            url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"
            response = requests.get(url, headers=headers, timeout=5)

            # Обновляем timestamp сразу после запроса
            config["last_update_check"] = datetime.utcnow().isoformat()

            # 4️⃣ 304 — ничего не изменилось
            if response.status_code == 304:
                save_user_config(config)
                self.update_not_found.emit()  # type: ignore
                return

            # 5️⃣ Ошибка API
            if response.status_code != 200:
                save_user_config(config)
                self.error_occurred.emit(f"GitHub API error: {response.status_code}")  # type: ignore
                return

            # 6️⃣ Сохраняем новый ETag
            new_etag = response.headers.get("ETag")
            if new_etag:
                config["update_etag"] = new_etag

            save_user_config(config)

            # 7️⃣ Обработка JSON
            data = response.json()
            latest_version = data.get("tag_name", "").lstrip("v")
            release_url = data.get("html_url", "")

            if not latest_version:
                self.error_occurred.emit("Invalid release data")  # type: ignore
                return

            # 8️⃣ Сравнение версий
            if version.parse(latest_version) > version.parse(__version__):
                self.update_available.emit(latest_version, release_url)  # type: ignore
            else:
                self.update_not_found.emit()  # type: ignore

        except Exception as e:
            self.error_occurred.emit(str(e))  # type: ignore
