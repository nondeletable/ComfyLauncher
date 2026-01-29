from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
    QPushButton,
    QStackedLayout,
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QSize, QUrl
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtMultimediaWidgets import QVideoWidget
from ui.theme.manager import THEME
from config import (
    DONATION_ICONS,
    CONTACT_ICONS,
    ABOUT_LOGO_BG,
    ABOUT_LOGO_ANIM,
)
import webbrowser


class AnimatedLogo(QWidget):
    SIZE = 180
    VIDEO_SIZE = 120

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(self.SIZE, self.SIZE)

        root = QStackedLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setStackingMode(QStackedLayout.StackingMode.StackAll)

        # ─── Background PNG ─────────────────────
        bg = QLabel()
        bg.setFixedSize(self.SIZE, self.SIZE)

        bg.setPixmap(QPixmap(ABOUT_LOGO_BG))
        bg.setScaledContents(True)

        # ─── Centered video container ───────────
        video_container = QWidget()
        video_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.video = QVideoWidget()
        self.video.setFixedSize(self.VIDEO_SIZE, self.VIDEO_SIZE)

        self.player = QMediaPlayer(self)
        self.player.setVideoOutput(self.video)
        self.player.setSource(QUrl.fromLocalFile(ABOUT_LOGO_ANIM))
        self.player.setLoops(QMediaPlayer.Loops.Infinite)
        self.player.play()

        video_layout.addWidget(self.video)

        root.addWidget(bg)
        root.addWidget(video_container)


class AboutSettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.colors = THEME.colors

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        # layout.setSpacing(24)

        # ─── LOGO + TITLE ────────────────────────────────
        header_layout = QHBoxLayout()
        header_layout.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )

        logo = AnimatedLogo()
        header_layout.addStretch()
        header_layout.addWidget(logo)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # div1 = QFrame()
        # div1.setFrameShape(QFrame.Shape.HLine)
        # div1.setStyleSheet(
        #     f"color: {self.colors['border_color']}; margin-top: 10px; margin-bottom: 10px;"
        # )
        # layout.addWidget(div1)

        # ─── ABOUT THE PROJECT ───────────────────────────────
        about_project = QLabel(
            "ComfyLauncher is designed to make launching and configuring ComfyUI simple and intuitive.\n"
            "It brings together everything you need - from build selection and path validation to theme customization.\n"
            "The core idea is comfort, clarity, and an easy start.\n\n"
            "ComfyLauncher was developed by Alexandra 'nondeletable'. I am a programmer who creates complete, ready-to-use applications.\n"
            "In my projects, I focus not only on functionality but also on visual harmony, high usability, and a cohesive interface.\n"
            "I want every tool to work out of the box and bring a sense of ease and enjoyment to its users.\n\n"
            "I’m open to collaborations and new opportunities. If you have an idea or need a Python developer to bring it to life, feel free to reach out.\n"
            "If you enjoy using ComfyLauncher, you can also support me with a tip - I would greatly appreciate it.\n"
            "Your support inspires me to continue creating helpful tools and improving my applications."
        )
        about_project.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        about_project.setWordWrap(True)
        about_project.setStyleSheet(
            f"color: {self.colors['text_primary']}; font-size: 14px;"
        )
        layout.addWidget(about_project)
        layout.addStretch(1)

        # ─── DONATION ICONS ─────────────────────────
        donate_layout = QHBoxLayout()
        donate_layout.setSpacing(20)
        donate_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addLayout(donate_layout)

        donations = [
            ("Boosty", DONATION_ICONS["boosty"], "https://boosty.to/codebird/donate"),
            # ("Patreon", DONATION_ICONS["patreon"], "https://patreon.com/CodeBird3001?utm_medium=unknown&utm_source=join_link&utm_campaign=creatorshare_creator&utm_content=copyLinkhttps://patreon.com/CodeBird3001?utm_medium=unknown&utm_source=join_link&utm_campaign=creatorshare_creator&utm_content=copyLink"),
            # ("Ko-fi", DONATION_ICONS["kofi"], "#"),
            # ("Buy Me a Coffee", DONATION_ICONS["buymeacoffee"], "#"),
        ]
        contacts = [
            ("GitHub", CONTACT_ICONS["github"], "https://github.com/nondeletable"),
            ("Email", CONTACT_ICONS["email"], "mailto:nondeletable@gmail.com"),
            ("Telegram", CONTACT_ICONS["telegram"], "https://t.me/nondeletable"),
            ("Discord", CONTACT_ICONS["discord"], "https://discord.gg/6nvXwXp78u"),
        ]

        for name, icon_path, url in donations:
            btn = QPushButton()
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(40, 40))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(f"{name}")
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: transparent;
                    border: 1px solid transparent;
                    border-radius: 6px;
                    padding: 6px;
                }}
                QPushButton:hover {{
                    background-color: {self.colors['accent_hover']};
                    border-color: {self.colors['accent']};
                    transform: scale(1.05);
                }}
            """
            )
            btn.clicked.connect(lambda _, link=url: self._open_link(link))  # type: ignore
            donate_layout.addWidget(btn)

        for name, icon_path, url in contacts:
            btn = QPushButton()
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(40, 40))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(f"{name}")
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: transparent;
                    border: 1px solid transparent;
                    border-radius: 6px;
                    padding: 6px;
                }}
                QPushButton:hover {{
                    background-color: {self.colors['accent_hover']};
                    border-color: {self.colors['accent']};
                    transform: scale(1.05);
                }}
            """
            )
            btn.clicked.connect(lambda _, link=url: self._open_link(link))  # type: ignore
            donate_layout.addWidget(btn)

        # ─── SIGNATURE BELOW ──────────────────────────
        footer = QLabel("Developed by nondeletable · v1.3.8 Beta · PyQt6 · 2025")
        footer.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        footer.setStyleSheet(
            f"color: {self.colors['text_secondary']}; font-size: 12px;"
        )
        layout.addStretch(1)
        layout.addWidget(footer)
        THEME.themeChanged.connect(self._apply_theme)

    # ─── Opening a link (stub) ─────────────────
    def _open_link(self, url: str):
        if url and url != "#":
            webbrowser.open(url)

    # ─── Repainting when changing the theme ────────
    def _apply_theme(self):
        self.colors = THEME.colors
        self.setStyleSheet(f"background-color: {self.colors['bg_header']};")
