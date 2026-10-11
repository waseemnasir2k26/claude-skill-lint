import json
from types import SimpleNamespace

from skill_lint.budget import NAME_ONLY, SEP, simulate, simulate_fixed
from skill_lint.model import ENTRY_CAP, Options, budget_for
from tests.helpers import FIX_PATHS, ROOT, mk, run

GOLDEN = ROOT / "tests" / "golden" / "budget_fixture.json"


def sk(name, n):
    return SimpleNamespace(name=name, description="x" * n, label=name)


def test_cost_constants():
    assert NAME_ONLY == 3 and SEP == 2


def test_budget_presets_follow_docs_fraction():
    assert budget_for("200k") == 8000
    assert budget_for("1m") == 40000
    assert budget_for("200k", 0.02) == 16000
    assert ENTRY_CAP == 1536


def test_everything_fits_nothing_dropped():
    b = simulate([sk("a", 100), sk("b", 100)], Options(budget_chars=1000))
    assert [e.status for e in b.entries] == ["full", "full"]
    assert b.total_full == 2 * (NAME_ONLY + 1 + SEP + 100) == b.total_after
    assert b.name_only == []


def test_descriptions_dropped_from_the_end_names_always_kept():
    skills = [sk("a", 100), sk("b", 100), sk("c", 100)]
    cost = NAME_ONLY + 1 + SEP + 100
    # room for names (3*4) + exactly two descriptions
    b = simulate(skills, Options(budget_chars=12 + 2 * (SEP + 100) + 5))
    assert [e.status for e in b.entries] == ["full", "full", "name-only"]
    assert len(b.entries) == 3 and b.total_after <= 12 + 2 * (SEP + 100) + 5
    assert b.entries[2].shown_len == 0 and cost == 106


def test_once_one_description_does_not_fit_later_ones_are_dropped_too():
    skills = [sk("a", 10), sk("b", 500), sk("c", 10)]
    b = simulate(skills, Options(budget_chars=60))
    assert [e.status for e in b.entries] == ["full", "name-only", "name-only"]


def test_names_alone_overflow_budget():
    b = simulate([sk("a", 50), sk("b", 50)], Options(budget_chars=3))
    assert all(e.status == "name-only" for e in b.entries) and b.uniform_fit_len == 0


def test_entry_cap_cuts_long_descriptions():
    b = simulate([sk("a", 3000)], Options(budget_chars=10000, entry_cap=1536))
    e = b.entries[0]
    assert e.status == "capped" and e.shown_len == 1536
    assert b.total_after == NAME_ONLY + 1 + SEP + 1536


def test_entry_cap_zero_means_unlimited():
    b = simulate([sk("a", 3000)], Options(budget_chars=10000, entry_cap=0))
    assert b.entries[0].status == "full" and b.entries[0].shown_len == 3000


def test_uniform_fit_len_is_exact():
    skills = [sk(f"s{i}", 400) for i in range(10)]
    names = 10 * (NAME_ONLY + 2)
    b = simulate(skills, Options(budget_chars=names + 10 * (SEP + 50)))
    assert b.uniform_fit_len == 50


def test_fix_recovers_chars_above_target():
    b = simulate([sk("a", 500), sk("b", 100)], Options(budget_chars=10000, target_len=200))
    assert [e.recovers for e in b.entries] == [300, 0]


def test_simulate_fixed_restores_descriptions():
    skills = [sk(f"s{i}", 600) for i in range(20)]
    o = Options(budget_chars=2000, target_len=40)
    before, after = simulate(skills, o), simulate_fixed(skills, o)
    assert len(after.described) > len(before.described)


def test_when_to_use_counts_toward_listing(tmp_path):
    mk(tmp_path, "x", description="Short but fine description text here.", extra_fm="when_to_use: " + "z" * 100 + "\n")
    r = run(tmp_path)
    assert len(r.skills[0].description) == 38 + 100


def test_budget_golden_on_fixture_pack():
    r = run(FIX_PATHS, budget_chars=700, target_len=60)
    got = r.ctx.budget().to_dict()
    after = simulate_fixed(r.skills, r.ctx.opts).to_dict()
    after.pop("entries")
    got["after_fix"] = after
    want = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert got == want
