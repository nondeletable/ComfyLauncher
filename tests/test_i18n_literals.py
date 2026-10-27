"""Translated files must not slip English text past ``t()``.

The check covers only the files already moved to ``t()``; every i18n block adds
its own, until the whole UI is listed. Strings without letters (``""``, ``"—"``)
are fine: there is nothing to translate in them.

Besides the calls that put text on screen, every string constant at module or
class level is suspect: it is evaluated once, so text there would stay in the
language of the first import. Identifier-like strings (i18n keys, config keys,
enum values: ``"settings.menu.builds"``, ``"manager"``) are not text; other
constants that are never shown (flags) are listed in ``_NOT_SHOWN``.
"""

import ast
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TRANSLATED = [
    "ui/settings/settings_window.py",
    "ui/settings/page_language.py",
    "ui/dialogs/setup_window.py",
    "ui/dialogs/messagebox.py",
    "main.py",
    "ui/dialogs/build_manager_dialog.py",
    "ui/dialogs/flags_picker_dialog.py",
    "ui/dialogs/webview2_setup.py",
    "ui/header.py",
    "ui/browser.py",
]

# Shown as-is in every language.
_PRODUCT_NAMES = {"ComfyLauncher"}

# Module/class constants that hold no interface text, per file.
_NOT_SHOWN = {
    "ui/dialogs/setup_window.py": {"DEFAULT_FLAGS"},
    # Preset names are flag names in all but spelling ("Low VRAM").
    "ui/dialogs/flags_picker_dialog.py": {"QUICK_PRESETS"},
}

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
_MESSAGE_BOX = {
    "info",
    "warning",
    "error",
    "ask_yes_no",
    "choose",
    "ask_exit",
    "update_available",
}
_MESSAGE_BOX_CLASS = {"MB", "MessageBox"}  # MB(title, text, kind)
_FILE_DIALOGS = {"getExistingDirectory", "getOpenFileName", "getSaveFileName"}


def _has_text(node) -> bool:
    """A literal (or f-string, or list of them) a user would read."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        if node.value in _PRODUCT_NAMES:
            return False
        return any(ch.isalpha() for ch in node.value)
    if isinstance(node, ast.JoinedStr):
        return any(_has_text(v) for v in node.values)
    if isinstance(node, (ast.List, ast.Tuple)):
        return any(_has_text(e) for e in node.elts)
    return False


_IDENTIFIER = re.compile(r"[a-z0-9_.]+")


def _has_constant_text(node) -> bool:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return not _IDENTIFIER.fullmatch(node.value) and _has_text(node)
    if isinstance(node, (ast.List, ast.Tuple)):
        return any(_has_constant_text(e) for e in node.elts)
    return _has_text(node)


def _constants(tree, allowed):
    """``NAME = "text"`` at module or class level, not inside functions."""
    bodies = [tree.body] + [n.body for n in tree.body if isinstance(n, ast.ClassDef)]
    for body in bodies:
        for node in body:
            if isinstance(node, ast.Assign):
                targets, value = node.targets, node.value
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                targets, value = [node.target], node.value
            else:
                continue
            names = {t.id for t in targets if isinstance(t, ast.Name)}
            if names - allowed and _has_constant_text(value):
                yield node


def _offenders(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in _constants(tree, _NOT_SHOWN.get(path, set())):
        yield f"{path}:{node.lineno}: {ast.unparse(node)[:80]}"
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
        if name in _TEXT_METHODS or name in _TEXT_WIDGETS:
            args = node.args
        elif name in _MESSAGE_BOX_CLASS:
            args = node.args[:2]
        elif name in _FILE_DIALOGS:
            args = node.args[1:2]  # the caption; the rest are a folder and filters
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
