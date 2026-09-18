"""stop_comfyui_hard must not cry wolf about a residual process.

Right after the kill the socket is still held for a moment, so a port check
there warned on every perfectly normal stop. The grace loop that follows is
what decides, and its verdict is the one that gets logged.
"""

import launcher


class FakeProc:
    def __init__(self, pid, cmdline):
        self.pid = pid
        self.info = {"pid": pid, "name": "python", "cmdline": cmdline}


def setup_stop(monkeypatch, port_states):
    """Run stop_comfyui_hard against a fake ComfyUI process.

    ``port_states`` is consumed one value per is_port_open() call; the last
    value repeats once exhausted.
    """
    build = "/tmp/fake-build"
    logs = []
    states = list(port_states)

    def fake_is_port_open(_port):
        return states.pop(0) if len(states) > 1 else states[0]

    monkeypatch.setattr(launcher, "log_event", logs.append)
    monkeypatch.setattr(launcher, "kill_process_tree", lambda pid: None)
    monkeypatch.setattr(launcher, "is_port_open", fake_is_port_open)
    monkeypatch.setattr(launcher, "get_listening_pids", lambda _port: [])
    monkeypatch.setattr(
        launcher.psutil,
        "process_iter",
        lambda _attrs: [FakeProc(4242, ["python", f"{build}/main.py"])],
    )
    return build, logs


def test_no_residual_warning_when_the_port_frees(monkeypatch):
    build, logs = setup_stop(monkeypatch, [True, False, False])

    launcher.stop_comfyui_hard(build, _grace_period=0.5)

    joined = "\n".join(logs)
    assert "residual" not in joined, joined
    assert "Port 8188 closed" in joined
    assert "process tree killed" in joined


def test_residual_warning_survives_for_a_real_leftover(monkeypatch):
    """The genuine warning must still fire — the point is to make it mean
    something, not to remove it."""
    build, logs = setup_stop(monkeypatch, [True])

    launcher.stop_comfyui_hard(build, _grace_period=0)

    joined = "\n".join(logs)
    assert "residual process remains" in joined, joined


def test_reports_when_there_was_nothing_to_kill(monkeypatch):
    build, logs = setup_stop(monkeypatch, [False])
    monkeypatch.setattr(launcher.psutil, "process_iter", lambda _attrs: [])

    launcher.stop_comfyui_hard(build, _grace_period=0)

    joined = "\n".join(logs)
    assert "No ComfyUI process found to stop" in joined
    assert "process tree killed" not in joined
