"""Translated files must not slip English text past ``t()``.

The check covers only the files already moved to ``t()``; every i18n block adds
its own, until the whole UI is listed. Strings without letters (``""``, ``"—"``)
are fine: there is nothing to translate in them.
"""

import ast
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TRANSLATED = [
    "ui/settings/settings_window.py",
    "ui/settings/page_language.py",
    "ui/dialogs/setup_window.py",
    "ui/dialogs/messagebox.py",
    "main.py",
]

# Calls whose text arguments reach the screen.
_TEXT_METHODS = {
    "setText",
    "setToolTip",
    "setWindowTitle",
    "setPlaceholderText",
    "addItem",
    "addItems",
    "insertItem",
    "setItemText",
}
_TEXT_WIDGETS = {"QLabel", "QPushButton", "QCheckBox", "QRadioButton", "QGroupBox"}
_MESSAGE_BOX = {"info", "warning", "error", "ask_yes_no", "choose"}


def _has_text(node) -> bool:
    """A literal (or f-string, or list of them) a user would read."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return any(ch.isalpha() for ch in node.value)
    if isinstance(node, ast.JoinedStr):
        return any(_has_text(v) for v in node.values)
    if isinstance(node, (ast.List, ast.Tuple)):
        return any(_has_text(e) for e in node.elts)
    return False


def _offenders(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        if name in _TEXT_METHODS or name in _TEXT_WIDGETS:
            args = node.args
        elif name in _MESSAGE_BOX:
            # (parent, title, text, ...): the rest are an icon kind and, for
            # choose(), (label, answer id) pairs whose ids are not shown.
            args = node.args[1:3]
            if name == "choose" and len(node.args) > 4:
                pairs = node.args[4]
                if isinstance(pairs, (ast.List, ast.Tuple)):
                    args += [p.elts[0] for p in pairs.elts if isinstance(p, ast.Tuple)]
        else:
            continue
        if any(_has_text(a) for a in args):
            yield f"{path}:{node.lineno}: {ast.unparse(node)[:80]}"


@pytest.mark.parametrize("path", TRANSLATED)
def test_no_untranslated_text(path):
    assert list(_offenders(path)) == []
