from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QScrollArea,
    QGridLayout,
    QFrame,
    QSizePolicy,
    QHBoxLayout,
    QFileDialog,
    QPushButton,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from ui.theme.manager import THEME, THEMES
from ui.theme.theme_importer import ThemeImporter
from ui.theme.theme_registry import REGISTRY
from utils.logger import log_event
import os
import webbrowser


class ColorThemesPage(QWidget):
    dirtyChanged = pyqtSignal(bool)
    """Application color theme selection page"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.selected_theme = THEME.name
        self.cards = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 20px;
                border-radius: 3px;
                margin-right: 8px;
                margin-left: 6px;
                margin-top: 12px;    
                margin-bottom: 12px;
            }
            QScrollBar::handle:vertical {
                background: #555555;
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: transparent;
            }
            """
        )

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(16)

        title = QLabel("Color Themes")
        title.setStyleSheet(
            f"color: {THEME.colors['text_primary']}; "
            f"font-size: 20px; font-weight: 600;"
        )
        content_layout.addWidget(title)

        self.grid = QGridLayout()
        self.grid.setSpacing(15)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.grid.setContentsMargins(14, 0, 0, 0)

        # create cards
        for i, name in enumerate(THEMES.keys()):
            card = self._create_theme_card(name)
            row, col = divmod(i, 4)
            self.grid.addWidget(card, row, col)
            self.cards[name] = card

        self._update_selection()
        self.selected_theme = THEME.name
        self._original_theme = THEME.name

        grid_container = QWidget()
        grid_container.setLayout(self.grid)
        content_layout.addWidget(grid_container)

        desc = QLabel(
            "Here you can select a launcher theme from a .json file.\n"
            "Or download a theme from https://www.comfyui-themes.com."
        )
        desc.setStyleSheet(f"color: {THEME.colors['text_secondary']}; font-size: 13px;")
        desc.setWordWrap(True)
        content_layout.addStretch()
        content_layout.addWidget(desc)

        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        btn_layout.setContentsMargins(14, 0, 0, 0)
        btn_layout.setSpacing(10)

        self.btn_select = QPushButton("Select")
        self.btn_select.setFixedSize(80, 35)
        self.btn_select.clicked.connect(self._load_custom_theme)  # type: ignore

        self.btn_download = QPushButton("Download")
        self.btn_download.setFixedSize(80, 35)
        self.btn_download.clicked.connect(self._open_comfyui_themes)  # type: ignore

        for btn in (self.btn_select, self.btn_download):
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: transparent;
                    border: 1px solid {THEME.colors['border_color']};
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background-color: {THEME.colors['accent']};
                    border-color: {THEME.colors['accent']};
                }}
                QPushButton:pressed {{
                    background-color: {THEME.colors['accent_hover']};
                }}
                """
            )
            btn_layout.addWidget(btn)

        self.btn_select.setToolTip("Select file")
        self.btn_download.setToolTip("Download from the website")

        content_layout.addLayout(btn_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)

    # ────────────────────────────────
    def _create_theme_card(self, name: str) -> QFrame:
        """Creates a preview card for a topic"""
        colors = THEMES[name]

        card = QFrame()
        card.setObjectName(name)
        card.setFixedSize(200, 120)
        card.setProperty("theme_name", name)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        card.setStyleSheet(
            f"""
            QFrame#{name} {{
                background-color: {colors['bg_header']};
                border: 1px solid {colors['accent']};
                border-radius: 8px;
            }}
            QFrame#{name}[selected="true"] {{
                border: 3px solid {colors['accent']};
            }}
            QFrame#{name}:hover {{
                border: 3px solid {colors['accent_hover']};
            }}
        """
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)

        # Top line - checkpoint + name
        row_top = QHBoxLayout()
        row_top.setSpacing(1)
        row_top.setAlignment(Qt.AlignmentFlag.AlignLeft)

        checkpoint = QLabel("●" if name == THEME.name else "○")
        checkpoint.setObjectName(f"chk_{name}")
        checkpoint.setStyleSheet(
            f""
            f"background-color: {colors['bg_header']}; "
            f"color: {colors['accent']}; font-size: 23px;"
        )

        pretty_name = name.replace("_", " ").title()
        label = QLabel(pretty_name, card)
        label.setStyleSheet(
            f"""
            background-color: {colors['bg_header']};
            color: {colors['text_primary']};
            font-weight: 400;
            font-size: 12px;
        """
        )

        row_top.addWidget(checkpoint)
        row_top.addWidget(label)
        layout.addLayout(row_top)

        # The bottom line is a preview of colors.
        row_bottom = QGridLayout()
        row_bottom.setSpacing(6)
        preview_keys = ["text_secondary", "accent", "text_primary"]
        for j, key in enumerate(preview_keys):
            block = QFrame()
            block.setFixedSize(42, 26)
            block.setStyleSheet(f"background-color: {colors[key]}; border-radius: 4px;")
            row_bottom.addWidget(block, 0, j)
        layout.addLayout(row_bottom)

        card.mousePressEvent = lambda e, n=name: self._on_theme_selected(n)
        return card

    # ────────────────────────────────
    def _on_theme_selected(self, theme_name: str):
        """Fires when the user selects a theme"""
        self.selected_theme = theme_name
        self._update_selection()
        is_changed = self.selected_theme != self._original_theme
        self.dirtyChanged.emit(is_changed)  # type: ignore[attr-defined]

    # ────────────────────────────────
    def _update_selection(self):
        """Updates the visual state of cards"""
        for name, card in self.cards.items():
            is_selected = name == self.selected_theme
            card.setProperty("selected", is_selected)
            card.style().unpolish(card)
            card.style().polish(card)

            checkpoint = card.findChild(QLabel, f"chk_{name}")
            if checkpoint:
                checkpoint.setText("●" if is_selected else "○")

    def is_dirty(self) -> bool:
        """Are there any unsaved changes"""
        return self.selected_theme != self._original_theme

    def _load_custom_theme(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select ComfyUI theme JSON", "", "JSON Files (*.json)"
        )
        if not path:
            return

        importer = ThemeImporter()
        theme_dict = importer.load(path)

        # avoid duplicates
        existing = REGISTRY.theme_exists(theme_dict)
        if existing:
            name = existing
        else:
            base = os.path.splitext(os.path.basename(path))[0]
            name = REGISTRY.add_custom(base.lower(), theme_dict)

        # create card
        card = self._create_theme_card(name)
        row = (len(self.cards)) // 4
        col = (len(self.cards)) % 4

        self.grid.addWidget(card, row, col)
        self.cards[name] = card

        # select new theme
        self._on_theme_selected(name)

    def apply(self):
        """Apply the selected theme"""
        try:
            THEME.switch(self.selected_theme)
            self._original_theme = self.selected_theme
            self.dirtyChanged.emit(False)  # type: ignore[attr-defined]

            # 🔹 After 100 ms, we close the window - closeEvent() will be triggered
            win = self.window()
            QTimer.singleShot(100, win.close)

            return True

        except Exception as e:
            log_event(f"Theme switch failed: {e}")
            return False

    def reset(self):
        """Cancel changes - return the selected theme to the active one"""
        self.selected_theme = self._original_theme
        self._update_selection()
        self.dirtyChanged.emit(False)  # type: ignore[attr-defined]

    def _open_comfyui_themes(self):
        webbrowser.open("https://www.comfyui-themes.com/")
