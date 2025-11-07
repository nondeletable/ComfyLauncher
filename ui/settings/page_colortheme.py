from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QGridLayout,
    QFrame,
    QSizePolicy,
    QHBoxLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from ui.theme.manager import THEME, THEMES


class ColorThemesPage(QWidget):
    dirtyChanged = pyqtSignal(bool)
    """Application color theme selection page"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.selected_theme = THEME.name
        self.cards = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(24)

        title = QLabel("Select color theme")
        title.setStyleSheet(
            f""
            f"color: {THEME.colors['text_primary']}; "
            f"font-size: 20px; font-weight: 500;"
        )
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(20)

        # create cards
        for i, name in enumerate(THEMES.keys()):
            card = self._create_theme_card(name)
            row, col = divmod(i, 2)
            grid.addWidget(card, row, col)
            self.cards[name] = card

        layout.addLayout(grid)
        layout.addStretch(1)
        self._update_selection()
        self.selected_theme = THEME.name
        self._original_theme = THEME.name

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
                border: 1px solid {colors['accent']};
            }}
            QFrame#{name}:hover {{
                border: 1px solid {colors['accent_hover']};
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
            print(f"Theme switch failed: {e}")
            return False

    def reset(self):
        """Cancel changes - return the selected theme to the active one"""
        self.selected_theme = self._original_theme
        self._update_selection()
        self.dirtyChanged.emit(False)  # type: ignore[attr-defined]
