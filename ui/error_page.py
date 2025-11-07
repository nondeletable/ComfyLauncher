from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt


class ErrorPage(QWidget):
    """ComfyUI Unavailable Error Widget"""

    def __init__(self, reload_callback):
        super().__init__()
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        label = QLabel("❌ Не удалось подключиться к ComfyUI")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ff5555;")

        btn = QPushButton("🔄 Повторить попытку")
        btn.setStyleSheet("padding: 8px 20px; font-size: 14px;")
        btn.clicked.connect(reload_callback)

        layout.addWidget(label)
        layout.addWidget(btn)
        self.setLayout(layout)
