from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QMovie, QScreen


class LauncherSplash(QWidget):
    """
    Полноценный splash-прелоадер лаунчера:
    - центрируется по экрану
    - не кликается (полностью игнорирует мышь)
    - всегда поверх всех окон
    - не закрывается до вызова finish()
    - аккуратный UI с анимацией и текстом
    """

    def __init__(self, gif_path: str, message: str = "Loading…"):
        super().__init__()

        # --- Основные флаги окна ---
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool  # делает окно поверх остальных, но не фокусируемым
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        # --- Основной контейнер ---
        self.setFixedSize(280, 320)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- Анимация GIF ---
        self.movie = QMovie(gif_path)
        self.gif_label = QLabel()
        self.gif_label.setMovie(self.movie)
        self.movie.start()

        # --- Текст статуса ---
        self.text_label = QLabel(message)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setStyleSheet(
            """
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
        """
        )

        layout.addWidget(self.gif_label)
        layout.addSpacing(10)
        layout.addWidget(self.text_label)

        # --- Фон карточки ---
        self.setStyleSheet(
            """
            background-color: rgba(30, 30, 30, 180);
            border-radius: 20px;
        """
        )

        self.center_on_screen()

    # ------------------------------
    # Центрирование
    # ------------------------------
    def center_on_screen(self):
        screen: QScreen = self.screen() or QApplication.primaryScreen()
        geo = screen.availableGeometry()

        center_x = geo.x() + (geo.width() - self.width()) // 2
        center_y = geo.y() + (geo.height() - self.height()) // 2
        self.move(center_x, center_y)

    # ------------------------------
    # Обновление текста
    # ------------------------------
    def update_message(self, elapsed_seconds: int):
        """Обновляет фазу и таймер на сплэше."""

        # --- Определяем фазу по времени ---
        if elapsed_seconds < 10:
            phase = "Preparing environment…"
        elif elapsed_seconds < 20:
            phase = "Initializing engine…"
        elif elapsed_seconds < 40:
            phase = "Loading core modules…"
        elif elapsed_seconds < 60:
            phase = "Starting server…"
        else:
            phase = "Almost ready…"

        # --- Обновляем текст ---
        self.text_label.setText(f"{phase}\n{elapsed_seconds} seconds")

    # ------------------------------
    # Завершение splash
    # ------------------------------
    def finish(self):
        self.close()
