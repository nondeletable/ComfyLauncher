import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import sys  # noqa: E402
import threading  # noqa: E402

import pytest  # noqa: E402

from ui import exception_hook as hook  # noqa: E402


def boom():
    try:
        raise ValueError("kaboom")
    except ValueError:
        return sys.exc_info()


@pytest.fixture
def shown(monkeypatch, tmp_path):
    """Record windows instead of opening them; keep crash files in tmp."""
    calls = []
    monkeypatch.setattr(
        hook,
        "_show_window",
        lambda e, t: calls.append((e, t, threading.current_thread())),
    )
    monkeypatch.setattr(hook.logger, "LOG_DIR", str(tmp_path))
    monkeypatch.setattr(hook, "_window_open", False)
    monkeypatch.setattr(hook, "_dispatcher", None)
    monkeypatch.setattr(hook, "_seen", {})
    return calls


def crash_files(tmp_path):
    return [p for p in os.listdir(tmp_path) if p.startswith("crash-")]


def test_install_sets_both_hooks(monkeypatch):
    monkeypatch.setattr(sys, "excepthook", sys.__excepthook__)
    monkeypatch.setattr(threading, "excepthook", threading.__excepthook__)
    hook.install_exception_hooks()
    assert sys.excepthook is hook._sys_hook
    assert threading.excepthook is hook._thread_hook


def test_before_the_window_is_enabled_a_crash_file_is_written(shown, tmp_path):
    hook._sys_hook(*boom())
    assert shown == []
    (name,) = crash_files(tmp_path)
    with open(os.path.join(tmp_path, name), encoding="utf-8") as f:
        text = f.read()
    assert "== TRACEBACK ==" in text and "kaboom" in text


def test_gui_thread_without_event_loop_shows_the_window_at_once(qapp, shown):
    hook.enable_report_window()
    hook._sys_hook(*boom())
    ((error, text, _thread),) = shown
    assert error == "ValueError: kaboom"
    assert "Traceback" in text


def test_background_thread_hands_over_to_the_gui_thread(qapp, shown):
    hook.enable_report_window()

    def worker():
        try:
            1 / 0
        except ZeroDivisionError:
            args = (*sys.exc_info(), threading.current_thread())
            hook._thread_hook(threading.ExceptHookArgs(args))

    t = threading.Thread(target=worker, name="worker")
    t.start()
    t.join()
    assert shown == []  # queued for the GUI thread, not run in the worker
    qapp.processEvents()
    ((error, _text, thread),) = shown
    assert error.startswith("ZeroDivisionError")
    assert thread is threading.main_thread()


def test_thread_hook_ignores_system_exit(shown, tmp_path):
    hook._thread_hook(threading.ExceptHookArgs((SystemExit, SystemExit(), None, None)))
    assert shown == [] and crash_files(tmp_path) == []


def test_keyboard_interrupt_goes_to_the_default_hook(shown, monkeypatch):
    passed = []
    monkeypatch.setattr(sys, "__excepthook__", lambda *a: passed.append(a[0]))
    hook._sys_hook(KeyboardInterrupt, KeyboardInterrupt(), None)
    assert passed == [KeyboardInterrupt] and shown == []


def test_no_second_window_while_one_is_open(qapp, shown, monkeypatch):
    hook.enable_report_window()
    monkeypatch.setattr(hook, "_window_open", True)
    hook._sys_hook(*boom())
    assert shown == []


def test_a_failing_window_falls_back_to_a_crash_file(qapp, monkeypatch, tmp_path):
    monkeypatch.setattr(hook.logger, "LOG_DIR", str(tmp_path))
    monkeypatch.setattr(hook, "_window_open", False)

    class Broken:
        active = None

        def __init__(self, *a, **k):
            raise RuntimeError("window is broken")

    monkeypatch.setattr("ui.dialogs.bug_report_dialog.BugReportDialog", Broken)
    hook._show_window("ValueError: kaboom", "Traceback ...")
    assert len(crash_files(tmp_path)) == 1
    assert hook._window_open is False


def test_a_failure_inside_the_hook_never_raises(shown, monkeypatch):
    def broken_log(_):
        raise OSError("log is gone")

    passed = []
    monkeypatch.setattr(hook, "log_event", broken_log)
    monkeypatch.setattr(sys, "__excepthook__", lambda *a: passed.append(a[0]))
    hook._sys_hook(*boom())
    assert passed == [ValueError]


def test_a_repeating_traceback_opens_the_window_once(qapp, shown, monkeypatch):
    logged = []
    monkeypatch.setattr(hook, "log_event", logged.append)
    hook.enable_report_window()
    for _ in range(9):
        hook._sys_hook(*boom())
    assert len(shown) == 1
    repeats = [line for line in logged if "repeated" in line]
    assert [line.split("(x")[1].split(")")[0] for line in repeats] == ["2", "4", "8"]


def test_a_different_traceback_still_gets_its_window(qapp, shown):
    hook.enable_report_window()
    hook._sys_hook(*boom())
    try:
        raise KeyError("other")
    except KeyError:
        hook._sys_hook(*sys.exc_info())
    assert len(shown) == 2


def test_no_exception_window_over_an_open_manual_one(qapp, monkeypatch):
    from ui.dialogs import bug_report_dialog as dlg_mod

    created = []

    class Fake:
        active = object()  # a manually opened report window

        def __init__(self, *a, **k):
            created.append(a)

    monkeypatch.setattr(dlg_mod, "BugReportDialog", Fake)
    monkeypatch.setattr(hook, "_window_open", False)
    hook._show_window("ValueError: kaboom", "Traceback ...")
    assert created == [] and hook._window_open is False


def test_manual_open_raises_the_window_already_open(qapp, monkeypatch):
    from ui.dialogs import bug_report_dialog as dlg_mod

    raised = []

    class Open:
        def raise_(self):
            raised.append("raise")

        def activateWindow(self):
            raised.append("activate")

    monkeypatch.setattr(dlg_mod.BugReportDialog, "active", Open())
    dlg_mod.open_bug_report(None, "manual")
    assert raised == ["raise", "activate"]


def test_crash_file_fallback_is_scrubbed(shown, tmp_path, monkeypatch):
    from utils import bug_report as br

    def fail(*a, **k):
        raise RuntimeError("collect failed")

    monkeypatch.setattr(br, "collect_report", fail)
    monkeypatch.setattr(
        br.Scrubber,
        "for_current_user",
        classmethod(lambda cls: cls(r"C:\Users\Jane", "Jane", "JANE-PC")),
    )
    hook._write_crash_file("E", r'File "C:\Users\Jane\x.py", line 1')
    (name,) = crash_files(tmp_path)
    with open(os.path.join(tmp_path, name), encoding="utf-8") as f:
        assert "Jane" not in f.read()
