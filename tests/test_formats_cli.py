import json
import re

import pytest

from skill_lint.cli import main
from skill_lint.report import FORMATS
from skill_lint.report import sarif as sarif_mod
from skill_lint.rules import RULES
from tests.helpers import FIX_PATHS, GOOD, mk, run


@pytest.fixture(scope="module")
def result():
    return run(FIX_PATHS)


def test_fifteen_rules_registered():
    assert sorted(RULES) == [f"SKL{n:03d}" for n in range(1, 16)]


def test_sarif_shape(result):
    doc = sarif_mod.to_obj(result, result.ctx.opts)
    assert doc["version"] == "2.1.0" and "$schema" in doc
    run0 = doc["runs"][0]
    drv = run0["tool"]["driver"]
    assert drv["name"] == "claude-skill-lint" and len(drv["rules"]) == 15
    ids = [r["id"] for r in drv["rules"]]
    assert run0["results"]
    for res in run0["results"]:
        assert res["ruleId"] in ids
        assert drv["rules"][res["ruleIndex"]]["id"] == res["ruleId"]
        assert res["level"] in ("error", "warning", "note")
        loc = res["locations"][0]["physicalLocation"]
        assert loc["region"]["startLine"] >= 1
        assert "\\" not in loc["artifactLocation"]["uri"]
        assert res["message"]["text"]


def test_sarif_is_valid_json_string(result):
    doc = json.loads(FORMATS["sarif"](result, result.ctx.opts))
    assert doc["runs"][0]["results"][0]["ruleId"].startswith("SKL")


def test_json_format_contents(result):
    doc = json.loads(FORMATS["json"](result, result.ctx.opts))
    assert doc["skills"] == 25
    assert doc["summary"]["errors"] == 3
    assert doc["collisions"][0]["a"] in ("doc-to-pdf", "md-to-pdf")
    assert doc["budget"]["skills"] == 24


def test_markdown_has_table_and_escapes_pipes(result):
    md = FORMATS["md"](result, result.ctx.opts)
    assert "| Severity | Rule | Location | Message |" in md
    assert "## Trigger collisions" in md


def test_html_escapes_and_is_self_contained(tmp_path):
    mk(tmp_path, "x", name="<script>alert(1)</script>", description="short")
    r = run(tmp_path)
    page = FORMATS["html"](r, r.ctx.opts)
    assert "<script>alert" not in page and "&lt;script&gt;" in page
    assert "http://" not in page and "https://" not in page


def test_text_format_has_budget_footer(result):
    out = FORMATS["text"](result, result.ctx.opts)
    assert "25 skills checked: 3 errors" in out
    assert "Skill listing budget: 8,000 chars" in out


def test_fix_suggestions_flag(capsys):
    main(["check", *map(str, FIX_PATHS), "--fix-suggestions", "--fail-on", "never"])
    assert "    fix: " in capsys.readouterr().out
    main(["check", *map(str, FIX_PATHS), "--fail-on", "never"])
    assert "    fix: " not in capsys.readouterr().out


def test_exit_codes(tmp_path):
    assert main(["check", *map(str, FIX_PATHS)]) == 1
    assert main(["check", *map(str, FIX_PATHS), "--fail-on", "never"]) == 0
    mk(tmp_path, "ok-skill", description=GOOD)
    assert main(["check", str(tmp_path), "--fail-on", "warning"]) == 0
    assert main(["check", str(tmp_path / "nothing-here")]) == 2


def test_context_flag_sets_budget(capsys):
    main(["budget", *map(str, FIX_PATHS), "--context", "1m", "--format", "json"])
    assert json.loads(capsys.readouterr().out)["budget_chars"] == 40000
    main(["budget", *map(str, FIX_PATHS), "--context", "1m", "--budget-chars", "1234", "--format", "json"])
    assert json.loads(capsys.readouterr().out)["budget_chars"] == 1234


def test_collisions_subcommand(capsys):
    assert main(["collisions", *map(str, FIX_PATHS)]) == 0
    out = capsys.readouterr().out
    assert "doc-to-pdf" in out and "md-to-pdf" in out
    main(["collisions", *map(str, FIX_PATHS), "--threshold", "0.99", "--format", "json"])
    assert json.loads(capsys.readouterr().out)[0]["shared_triggers"]


def test_report_subcommand_writes_html(tmp_path):
    out = tmp_path / "r.html"
    assert main(["report", *map(str, FIX_PATHS), "--out", str(out)]) == 0
    assert out.read_text(encoding="utf-8").startswith("<!doctype html>")


def test_rules_subcommand(capsys):
    main(["rules"])
    out = capsys.readouterr().out
    assert len(re.findall(r"^SKL\d{3}", out, re.M)) == 15


def test_check_output_file(tmp_path):
    out = tmp_path / "o.sarif"
    main(["check", *map(str, FIX_PATHS), "--format", "sarif", "-o", str(out), "--fail-on", "never"])
    assert json.loads(out.read_text(encoding="utf-8"))["version"] == "2.1.0"
