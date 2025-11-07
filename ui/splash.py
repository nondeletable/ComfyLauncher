from PyQt6.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QPixmap, QMovie
from PyQt6.QtCore import Qt


class AnimatedSplash(QSplashScreen):
    """Animated splash with a spinner"""

    def __init__(self, gif_path, message):
        super().__init__(QPixmap(1, 1))
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowOpacity(0.95)

        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.movie = QMovie(gif_path)
        self.label = QLabel()
        self.label.setMovie(self.movie)
        self.movie.start()

        self.text = QLabel(message)
        self.text.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        self.text.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.label)
        layout.addWidget(self.text)
        container.setLayout(layout)

        self.resize(220, 270)
        self.setStyleSheet("background-color: #353535; border-radius: 15px;")

    def update_message(self, seconds, max_seconds):
        """Updates the timeout message"""
        self.text.setText(f"Launching ComfyUI... \n{seconds} / {max_seconds} s")
