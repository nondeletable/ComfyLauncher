import json
import os
import sys
from urllib.parse import parse_qs, urlparse

import pytest

from utils import bug_report as br
from utils.console_buffer import ConsoleBuffer

HOME_TOKEN = "%USERPROFILE%" if sys.platform == "win32" else "~"


@pytest.fixture
def scrub():
    return br.Scrubber(r"C:\Users\Jane.Doe", "Jane.Doe", "JANE-PC")


def test_home_folder_is_replaced_in_any_spelling(scrub):
    for path in (
        r"C:\Users\Jane.Doe\ComfyUI\main.py",
        "C:/Users/Jane.Doe/ComfyUI/main.py",
        r"c:\users\jane.doe\ComfyUI\main.py",
        r"C:\\Users\\Jane.Doe\\ComfyUI\\main.py",
    ):
        out = scrub(path)
        assert "Jane" not in out and "jane" not in out
        assert out.startswith(HOME_TOKEN)


def test_home_prefix_of_a_longer_folder_is_not_mistaken_for_home(scrub):
    out = scrub(r"C:\Users\Jane.Doe2\file.txt")
    assert out == r"C:\Users\<user>\file.txt"


def test_other_profile_folders_lose_the_owner_name(scrub):
    assert scrub(r"D:\x C:\Users\Bob\a") == r"D:\x C:\Users\<user>\a"
    assert scrub("/home/bob/ComfyUI") == "/home/<user>/ComfyUI"


def test_user_and_host_names_are_replaced(scrub):
    out = scrub("user jane.doe on JANE-PC, jane-pc again")
    assert out == "user <user> on <host>, <host> again"


def test_names_inside_flags_and_words_survive():
    scrub = br.Scrubber(None, "max", "box")
    assert scrub("--max-upload-size 10 maximize sandbox") == (
        "--max-upload-size 10 maximize sandbox"
    )
    assert scrub("hello max") == "hello <user>"


def test_linux_home_is_replaced():
    scrub = br.Scrubber("/home/jane", None, None)
    assert scrub("/home/jane/ComfyUI") == f"{HOME_TOKEN}/ComfyUI"


def test_scrub_data_reaches_keys_and_nested_values(scrub):
    data = {r"C:\Users\Jane.Doe\b": [{"path": "C:/Users/Jane.Doe/x"}], "n": 3}
    out = scrub.scrub_data(data)
    assert json.dumps(out).count("Jane") == 0
    assert out["n"] == 3


@pytest.fixture
def fake_env(tmp_path, monkeypatch):
    """A config, a log and a console buffer that all leak the user name."""
    home = tmp_path / "Users" / "Jane"
    build = home / "ComfyUI_portable" / "ComfyUI"
    build.mkdir(parents=True)
    cfg_path = tmp_path / "user_config.json"
    cfg_path.write_text(
        json.dumps(
            {
                "comfyui_path": str(build),
                "last_used_build_id": "b1",
                "builds": [{"id": "b1", "path": str(build), "extra_flags": ["--cpu"]}],
                "update_etag": "W/secret",
                "last_update_check": "2026-01-01",
                "theme": "dracula",
                "show_cmd": False,
            }
        ),
        encoding="utf-8",
    )
    log_path = tmp_path / "launcher.log"
    log_path.write_text(
        "".join(f"line {i}\n" for i in range(br.LOG_TAIL_LINES + 50))
        + f"opened {build}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr("config.USER_CONFIG_PATH", str(cfg_path))
    monkeypatch.setattr("utils.logger.LOG_FILE", str(log_path))
    ConsoleBuffer.clear()
    ConsoleBuffer.add(f"Total VRAM 24564 MB, cwd {build}\n")
    yield br.Scrubber(str(home), "Jane", "JANE-PC")
    ConsoleBuffer.clear()


def test_collected_report_is_scrubbed_everywhere(fake_env):
    report = br.collect_report(
        "error_screen", "PROCESS_START_FAILED", scrubber=fake_env
    )
    text = br.render_report(report, comment="it broke")
    assert "Jane" not in text
    assert "W/secret" not in text and "last_update_check" not in text
    assert '"theme": "dracula"' in text
    assert "Total VRAM 24564 MB" in text
    assert "it broke" in text


def test_summary_carries_the_diagnosis_fields(fake_env):
    report = br.collect_report("manual", scrubber=fake_env)
    summary = dict(report.summary)
    assert summary["Launch flags"] == "--cpu"
    assert summary["Theme"] == "dracula"
    assert summary["Console"] == "internal"
    assert summary["Where"] == "Reported manually"
    assert summary["Launcher version"]


def test_log_is_cut_to_its_tail(fake_env):
    report = br.collect_report("manual", scrubber=fake_env)
    log = report.sections[br.SECTION_LOG]
    assert len(log.splitlines()) == br.LOG_TAIL_LINES
    assert "line 0\n" not in log


def test_sections_can_be_left_out(fake_env):
    report = br.collect_report("exception", traceback_text="Traceback: boom")
    text = br.render_report(report, include={br.SECTION_CONFIG})
    assert "== TRACEBACK ==" in text and "boom" in text
    assert "== CONFIG ==" in text
    assert "LAUNCHER LOG" not in text and "COMFYUI CONSOLE" not in text


def test_empty_sections_are_marked_not_dropped(fake_env):
    ConsoleBuffer.clear()
    text = br.render_report(br.collect_report("manual", scrubber=fake_env))
    assert br.extract_section(text, br.SECTION_CONSOLE) == "(empty)"


def test_missing_config_and_log_do_not_raise(tmp_path, monkeypatch):
    monkeypatch.setattr("config.USER_CONFIG_PATH", str(tmp_path / "none.json"))
    monkeypatch.setattr("utils.logger.LOG_FILE", str(tmp_path / "none.log"))
    text = br.render_report(br.collect_report("manual"))
    assert "(no config file)" in text and "(no log file)" in text


def test_extract_section_returns_one_body(fake_env):
    text = br.render_report(br.collect_report("manual", scrubber=fake_env))
    summary = br.extract_section(text, br.SECTION_SUMMARY)
    assert summary.startswith("Launcher version:")
    assert "== " not in summary
    assert br.extract_section(text, "NOPE") == ""


def test_issue_url_is_prefilled():
    url = br.github_issue_url("[Report] x", "body text")
    parts = urlparse(url)
    assert parts.netloc == "github.com"
    assert parts.path == f"/{br.GITHUB_REPO}/issues/new"
    q = parse_qs(parts.query)
    assert q["title"] == ["[Report] x"]
    assert q["body"] == ["body text"]
    assert q["labels"] == ["bug,report"]


@pytest.mark.parametrize("line", ["x" * 200, "ж" * 200])
def test_long_issue_body_is_cut_to_the_limit(line):
    body = "\n".join([line] * 200)
    url = br.github_issue_url("t", body, limit=3000)
    assert len(url) <= 3000
    assert (
        "full text is in the attached file" in parse_qs(urlparse(url).query)["body"][0]
    )


def test_single_huge_line_is_cut_too():
    url = br.github_issue_url("t", "y" * 20000, limit=2000)
    assert len(url) <= 2000


def test_issue_title_and_body():
    assert br.issue_title("") == "[Report] Problem report"
    assert br.issue_title("   ") == "[Report] Problem report"
    assert br.issue_title("Boom\nmore") == "[Report] Boom"
    assert len(br.issue_title("z" * 300)) == 100
    body = br.issue_body("== SUMMARY ==\nA: b\n\n== CONFIG ==\n{}\n", "r.txt")
    assert "r.txt" in body and "A: b" in body and "CONFIG" not in body


def test_save_report_writes_utf8(tmp_path):
    path = br.save_report("отчёт\n", str(tmp_path))
    assert os.path.basename(path).startswith("comfylauncher-report-")
    assert path.endswith(".txt")
    with open(path, encoding="utf-8") as f:
        assert f.read() == "отчёт\n"
