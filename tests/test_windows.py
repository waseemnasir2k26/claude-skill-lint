"""Windows-path and line-ending handling. These run on every OS; they test the logic, not the platform."""
from pathlib import PureWindowsPath

from skill_lint.model import display_path
from tests.helpers import GOOD, mk, run


def test_crlf_file_parses_and_lints(tmp_path):
    raw = ("---\r\nname: crlf-skill\r\ndescription: " + GOOD + "\r\n---\r\n\r\n# Body\r\n").encode()
    mk(tmp_path, "crlf-skill", raw=raw)
    r = run(tmp_path)
    assert r.skills[0].name == "crlf-skill"
    assert r.findings == []


def test_bom_file_parses(tmp_path):
    raw = b"\xef\xbb\xbf---\nname: bom-skill\ndescription: " + GOOD.encode() + b"\n---\nbody\n"
    mk(tmp_path, "bom-skill", raw=raw)
    r = run(tmp_path)
    assert r.skills[0].present and r.findings == []


def test_backslash_link_resolves(tmp_path):
    mk(tmp_path, "x", description=GOOD, body="See [g](references\\guide.md)\n")
    (tmp_path / "x" / "references").mkdir()
    (tmp_path / "x" / "references" / "guide.md").write_text("hi")
    assert not any(f.rule == "SKL009" for f in run(tmp_path).findings)


def test_windows_user_path_flagged_with_any_slash(tmp_path):
    mk(tmp_path, "x", description=GOOD, body="a C:\\Users\\alice\\x and b D:/Users/bob/y\n")
    msgs = [f.message for f in run(tmp_path).findings if f.rule == "SKL010"]
    assert len(msgs) == 1  # one finding per line
    mk(tmp_path, "y", description=GOOD, body="only D:/Users/bob/y here\n")
    assert len([f for f in run(tmp_path).findings if f.rule == "SKL010"]) == 2


def test_findings_use_forward_slashes(tmp_path):
    mk(tmp_path, "BAD_Name", description="tiny")
    r = run(tmp_path)
    assert r.findings and all("\\" not in f.path for f in r.findings)


def test_display_path_posix_style(tmp_path):
    p = tmp_path / "a" / "b" / "SKILL.md"
    p.parent.mkdir(parents=True)
    p.write_text("x")
    assert "\\" not in display_path(p)
    assert display_path(p).endswith("a/b/SKILL.md")


def test_pure_windows_path_semantics_documented():
    # sanity check of the assumption behind display_path: PureWindowsPath.as_posix swaps separators
    assert PureWindowsPath("C:\\Users\\x\\SKILL.md").as_posix() == "C:/Users/x/SKILL.md"


def test_home_is_shown_as_tilde(tmp_path, monkeypatch):
    home, cwd = tmp_path / "home", tmp_path / "cwd"
    cwd.mkdir()
    monkeypatch.setattr("pathlib.Path.home", classmethod(lambda cls: home))
    monkeypatch.chdir(cwd)
    d = home / ".claude" / "skills" / "z" / "SKILL.md"
    d.parent.mkdir(parents=True)
    d.write_text("x")
    assert display_path(d) == "~/.claude/skills/z/SKILL.md"


def test_case_variant_folder_dedupes_same_file(tmp_path):
    mk(tmp_path, "x", description=GOOD)
    r = run([tmp_path, tmp_path / "x" / "SKILL.md"])
    assert len(r.skills) == 1
