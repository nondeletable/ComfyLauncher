from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
    QPushButton,
    QFrame,
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QSize
from ui.theme.manager import THEME
from config import ICON_PATH, DONATION_ICONS, CONTACT_ICONS
import webbrowser


class AboutSettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.colors = THEME.colors

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(24)

        # ─── LOGO + TITLE ────────────────────────────────
        header_layout = QHBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        header_layout.setSpacing(8)

        logo = QLabel()
        pix = QPixmap(ICON_PATH).scaled(
            40, 40,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        logo.setPixmap(pix)
        logo.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        title = QLabel("ComfyLauncher")
        title.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        title.setStyleSheet(
            f"""
            font-size: 20px;
            font-weight: 600;
            color: {self.colors['text_primary']};
        """
        )

        header_layout.addWidget(logo)
        header_layout.addWidget(title)

        layout.addLayout(header_layout)

        div1 = QFrame()
        div1.setFrameShape(QFrame.Shape.HLine)
        div1.setStyleSheet(
            f"color: {self.colors['border_color']}; margin-top: 10px; margin-bottom: 10px;"
        )
        layout.addWidget(div1)

        # ─── ABOUT THE PROJECT ───────────────────────────────
        about_project = QLabel(
            "ComfyLauncher is designed to make launching and configuring ComfyUI simple and intuitive.\n"
            "It brings together everything you need - from build selection and path validation to theme customization.\n"
            "The core idea is comfort, clarity, and an easy start."
        )
        about_project.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        about_project.setWordWrap(True)
        about_project.setStyleSheet(
            f"color: {self.colors['text_primary']}; font-size: 14px;"
        )
        layout.addWidget(about_project)

        div2 = QFrame()
        div2.setFrameShape(QFrame.Shape.HLine)
        div2.setStyleSheet(
            f"color: {self.colors['border_color']}; margin-top: 10px; margin-bottom: 10px;"
        )
        layout.addWidget(div2)

        # ─── ABOUT THE DEVELOPER ─────────────────────────
        about_dev = QLabel(
            "ComfyLauncher was developed by Alexandra 'CodeBird'. I am a programmer who creates complete, ready-to-use applications.\n"
            "In my projects, I focus not only on functionality but also on visual harmony, high usability, and a cohesive interface.\n"
            "I want every tool to work out of the box and bring a sense of ease and enjoyment to its users.\n\n"
            "I am a beginner developer, and if you have any ideas or need a Python developer to bring them to life, you can contact me.\n"
            "If you enjoy using ComfyLauncher, you can also support me with a tip — I would greatly appreciate it.\n"
            "Your support inspires me to continue creating helpful tools and improving my applications."
        )
        about_dev.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        about_dev.setWordWrap(True)
        about_dev.setStyleSheet(
            f"color: {self.colors['text_primary']}; font-size: 14px;"
        )
        layout.addWidget(about_dev)

        # ─── DONATION ICONS ─────────────────────────
        donate_layout = QHBoxLayout()
        donate_layout.setSpacing(16)
        donate_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addLayout(donate_layout)

        donations = [
            ("Boosty", DONATION_ICONS["boosty"], "https://boosty.to/codebird/donate"),
            # ("Patreon", DONATION_ICONS["patreon"], "https://patreon.com/CodeBird3001?utm_medium=unknown&utm_source=join_link&utm_campaign=creatorshare_creator&utm_content=copyLinkhttps://patreon.com/CodeBird3001?utm_medium=unknown&utm_source=join_link&utm_campaign=creatorshare_creator&utm_content=copyLink"),
            # ("Ko-fi", DONATION_ICONS["kofi"], "#"),
            # ("Buy Me a Coffee", DONATION_ICONS["buymeacoffee"], "#"),
        ]
        contacts = [
            ("GitHub", CONTACT_ICONS["github"], "https://github.com/SkriptSparrow"),
            ("Email", CONTACT_ICONS["email"], "mailto:codebird.dev@gmail.com"),
            ("Telegram", CONTACT_ICONS["telegram"], "https://t.me/Alex_Gicheva"),
            ("Discord", CONTACT_ICONS["discord"], "https://discordapp.com/users/CodeBird#7231"),
        ]

        for name, icon_path, url in donations:
            btn = QPushButton()
            btn.setIcon(QIcon(icon_path))
            btn.setIconSize(QSize(32, 32))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(f"My {name}")
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
            btn.setIconSize(QSize(32, 32))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setToolTip(f"My {name}")
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

        layout.addSpacing(15)

        # ─── SIGNATURE BELOW ──────────────────────────
        footer = QLabel("Developed by CodeBird · Version 1.0.0 · PyQt6 · 2025")
        footer.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        footer.setStyleSheet(
            f"color: {self.colors['text_secondary']}; font-size: 12px; margin-top: 20px;"
        )
        layout.addWidget(footer)

        layout.addStretch()
        THEME.themeChanged.connect(self._apply_theme)

    # ─── Opening a link (stub) ─────────────────
    def _open_link(self, url: str):
        if url and url != "#":
            webbrowser.open(url)

    # ─── Repainting when changing the theme ────────
    def _apply_theme(self):
        self.colors = THEME.colors
        self.setStyleSheet(f"background-color: {self.colors['bg_header']};")
