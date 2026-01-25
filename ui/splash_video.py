from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QApplication
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from utils.logger import log_event
from config import ICON_PATH


class LauncherSplashVideo(QWidget):
    """
    Splash screen with MP4 (H.264) video.
    Scales by screen height, keeps aspect ratio, centered.
    """

    ASPECT_RATIO = 1618 / 616  # выбранный ролик

    def __init__(self, video_path: str):
        super().__init__()

        self.setWindowIcon(QIcon(ICON_PATH))

        # ─── Window flags ─────────────────────────────
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )

        # ─── Layout ──────────────────────────────────
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ─── Video widget ────────────────────────────
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: transparent;")
        self.video_widget.setAspectRatioMode(Qt.AspectRatioMode.IgnoreAspectRatio)
        layout.addWidget(self.video_widget, stretch=1)

        # ─── Media player ────────────────────────────
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.audio.setMuted(True)

        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video_widget)

        # ─── Geometry ────────────────────────────────
        self.resize_for_screen()
        self.center_on_screen()

        # ─── Show the window BEFORE loading the video ───
        self.show()

        # ─── Load and play videos ───────────────────
        # Use QTimer to let the window render
        QTimer.singleShot(100, lambda: self._load_and_play(video_path))

        # Connecting signals for debugging
        self.player.errorOccurred.connect(self._on_error)

        # Looping a video
        self.player.setLoops(QMediaPlayer.Loops.Infinite)

    def _load_and_play(self, video_path: str):
        """Downloads and plays videos"""
        url = QUrl.fromLocalFile(video_path)
        log_event(f"Loading video from: {url.toString()}")
        self.player.setSource(url)
        self.player.play()

    def _on_error(self, error, error_string):
        """Media player error handler"""
        log_event(f"Media player error: {error}")
        log_event(f"Error string: {error_string}")

    # ────────────────────────────────────────────────
    def resize_for_screen(self):
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()

        screen_h = screen_rect.height()

        # 25% of the screen height
        target_h = int(screen_h * 0.25)
        aspect = 1618 / 616
        target_w = int(target_h * aspect)

        # Set the size only for the main window
        self.setFixedSize(target_w, target_h)

    def center_on_screen(self):
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        geo = self.frameGeometry()
        geo.moveCenter(screen_rect.center())
        self.move(geo.topLeft())

    # ------------------------------
    # Splash completion
    # ------------------------------
    def finish(self):
        self.player.stop()
        self.close()
