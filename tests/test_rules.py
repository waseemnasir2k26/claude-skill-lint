import os

import pytest

from tests.helpers import FIX_PATHS, GOOD, mk, run, rules_for


@pytest.fixture(scope="module")
def fixture_result():
    return run(FIX_PATHS)


def test_fixture_pack_has_25_skills(fixture_result):
    assert len(fixture_result.skills) == 25


@pytest.mark.parametrize("folder", ["pdf-form-filler", "csv-cleaner", "git-commit-writer", "sql-review", "api-doc-generator"])
def test_clean_fixtures_have_no_findings(fixture_result, folder):
    assert rules_for(fixture_result, folder) == set()


@pytest.mark.parametrize("folder,rule", [
    ("no-frontmatter", "SKL001"),
    ("missing-description", "SKL001"),
    ("colon-yaml", "SKL001"),
    ("bad-name-case", "SKL002"),
    ("name-mismatch", "SKL002"),
    ("calendar-wrangler", "SKL003"),
    ("tiny-desc", "SKL003"),
    ("vague-helper", "SKL004"),
    ("no-triggers", "SKL005"),
    ("doc-to-pdf", "SKL006"),
    ("late-trigger", "SKL007"),
    ("calendar-wrangler", "SKL007"),
    ("big-body", "SKL008"),
    ("dead-links", "SKL009"),
    ("personal-paths", "SKL010"),
    ("leaked-secret", "SKL011"),
    ("report-builder", "SKL012"),
    ("md-to-pdf", "SKL013"),
    ("bad-script", "SKL014"),
    ("first-person", "SKL015"),
])
def test_each_rule_fires_on_its_fixture(fixture_result, folder, rule):
    assert rule in rules_for(fixture_result, folder)


def test_dead_links_reports_both_missing_files(fixture_result):
    msgs = [f.message for f in fixture_result.findings if f.rule == "SKL009"]
    assert any("references/guide.md" in m for m in msgs)
    assert any("scripts/scan.py" in m for m in msgs)
    assert not any("example.com" in m for m in msgs)


def test_secret_value_is_redacted(fixture_result):
    f = next(f for f in fixture_result.findings if f.rule == "SKL011")
    assert "k9f3a7c1" not in f.message and f.severity == "error"


def test_valid_links_do_not_fire(fixture_result):
    assert "SKL009" not in rules_for(fixture_result, "pdf-form-filler")
    assert "SKL009" not in rules_for(fixture_result, "api-doc-generator")


def test_ignore_option_skips_rule(tmp_path):
    mk(tmp_path, "x", description="tiny")
    assert any(f.rule == "SKL003" for f in run(tmp_path).findings)
    assert not any(f.rule == "SKL003" for f in run(tmp_path, ignore=("SKL003",)).findings)


def test_skl001_non_string_description(tmp_path):
    mk(tmp_path, "x", description="[a, b]")
    assert any(f.rule == "SKL001" and "must be a string" in f.message for f in run(tmp_path).findings)


def test_skl001_name_too_long(tmp_path):
    n = "a" * 70
    mk(tmp_path, n, description=GOOD)
    assert any(f.rule == "SKL001" and "64" in f.message for f in run(tmp_path).findings)


def test_skl003_hard_limit_is_error(tmp_path):
    mk(tmp_path, "x", description='"' + "word " * 400 + '"')
    f = [f for f in run(tmp_path).findings if f.rule == "SKL003"][0]
    assert f.severity == "error" and "1536" in f.message


def test_skl003_spec_limit_is_warning_below_entry_cap(tmp_path):
    mk(tmp_path, "x", description='"' + "word " * 250 + '"')
    f = [f for f in run(tmp_path).findings if f.rule == "SKL003"][0]
    assert f.severity == "warning" and "1024" in f.message


def test_skl003_respects_custom_limit(tmp_path):
    mk(tmp_path, "x", description=GOOD)
    assert not any(f.rule == "SKL003" for f in run(tmp_path).findings)
    assert any(f.rule == "SKL003" for f in run(tmp_path, desc_warn=50).findings)


def test_skl004_word_boundary(tmp_path):
    mk(tmp_path, "x", description='Parses miscellaneousfree input. Use when the user says "parse logs" daily.')
    assert not any(f.rule == "SKL004" for f in run(tmp_path).findings)


def test_skl005_accepts_quoted_phrases_without_marker(tmp_path):
    mk(tmp_path, "x", description='Formats changelogs, handles "keep a changelog" style and "release notes" output.')
    assert not any(f.rule == "SKL005" for f in run(tmp_path).findings)


def test_skl006_cleared_by_do_not_use(tmp_path):
    d = 'Convert Markdown documents to PDF with contents. Use when the user asks to "convert markdown to pdf". Do NOT use for slides.'
    mk(tmp_path, "a", description=d)
    mk(tmp_path, "b", description=d)
    r = run(tmp_path)
    assert any(f.rule == "SKL013" for f in r.findings)
    assert not any(f.rule == "SKL006" for f in r.findings)


def test_skl007_cutoff_is_configurable(tmp_path):
    mk(tmp_path, "x", description='Manage warehouse stock levels, cycle counts and reorder points across sites. Use when the user says "count stock".')
    assert not any(f.rule == "SKL007" for f in run(tmp_path).findings)
    assert any(f.rule == "SKL007" for f in run(tmp_path, cutoff=20).findings)


def test_skl008_token_limit(tmp_path):
    mk(tmp_path, "x", description=GOOD, body="word " * 6000)
    assert any(f.rule == "SKL008" and "tokens" in f.message for f in run(tmp_path).findings)


def test_skl009_ignores_code_fences(tmp_path):
    mk(tmp_path, "x", description=GOOD, body="```\n[x](nope.md)\n```\n")
    assert not any(f.rule == "SKL009" for f in run(tmp_path).findings)


def test_skl009_handles_anchor_and_existing_file(tmp_path):
    mk(tmp_path, "x", description=GOOD, body="[a](ref.md#top) [b](#local) [c](mailto:a@b.co)\n")
    (tmp_path / "x" / "ref.md").write_text("hi")
    assert not any(f.rule == "SKL009" for f in run(tmp_path).findings)


def test_skl010_unix_and_mac_paths(tmp_path):
    mk(tmp_path, "x", description=GOOD, body="/Users/alice/code/tool\n/home/bob/x\n")
    assert len([f for f in run(tmp_path).findings if f.rule == "SKL010"]) == 2


def test_skl010_placeholders_ignored(tmp_path):
    mk(tmp_path, "x", description=GOOD, body="Use /home/user/project and C:\\Users\\you\\file\n")
    assert not any(f.rule == "SKL010" for f in run(tmp_path).findings)


def test_skl011_provider_patterns_built_at_runtime(tmp_path):
    key = "AK" + "IA" + "ABCDEFGHIJKLMNOP"
    tok = "gh" + "p_" + "a1b2c3d4e5" * 4
    mk(tmp_path, "x", description=GOOD, body=f"aws {key}\ngh {tok}\n")
    msgs = [f.message for f in run(tmp_path).findings if f.rule == "SKL011"]
    assert len(msgs) == 2 and all("***" in m for m in msgs)
    assert not any(key in m or tok in m for m in msgs)


def test_skl011_placeholder_values_not_flagged(tmp_path):
    mk(tmp_path, "x", description=GOOD, body='api_key = "your-api-key-goes-here-123"\ntoken: ${GITHUB_TOKEN_VALUE_1234}\n')
    assert not any(f.rule == "SKL011" for f in run(tmp_path).findings)


def test_skl012_same_file_twice_is_not_duplicate(tmp_path):
    mk(tmp_path, "x", description=GOOD)
    r = run([tmp_path, tmp_path])
    assert not any(f.rule == "SKL012" for f in r.findings)


def test_skl014_good_script_passes(tmp_path):
    mk(tmp_path, "x", description=GOOD)
    s = tmp_path / "x" / "scripts"
    s.mkdir()
    (s / "go.sh").write_text("#!/usr/bin/env bash\necho hi\n")
    os.chmod(s / "go.sh", 0o755)
    assert not any(f.rule == "SKL014" for f in run(tmp_path).findings)


def test_skl014_missing_shebang(tmp_path):
    mk(tmp_path, "x", description=GOOD)
    s = tmp_path / "x" / "scripts"
    s.mkdir()
    (s / "go.py").write_text("print('hi')\n")
    assert any(f.rule == "SKL014" and "shebang" in f.message for f in run(tmp_path).findings)


@pytest.mark.parametrize("desc", ["I help you write emails and I will polish them for you.",
                                  "You are an expert reviewer who checks pull requests."])
def test_skl015_first_person(tmp_path, desc):
    mk(tmp_path, "x", description=desc)
    assert any(f.rule == "SKL015" for f in run(tmp_path).findings)


def test_skl015_third_person_ok(tmp_path):
    mk(tmp_path, "x", description=GOOD)
    assert not any(f.rule == "SKL015" for f in run(tmp_path).findings)
