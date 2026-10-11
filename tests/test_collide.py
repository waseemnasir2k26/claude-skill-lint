import math

from skill_lint.collide import cosine, find_collisions, idf_table, jaccard, tfidf_vec
from skill_lint.textutil import first_trigger_pos, tokens, trigger_phrases


class S:
    def __init__(self, name, description):
        self.name, self.description = name, description

    @property
    def label(self):
        return self.name


def test_jaccard_exact_values():
    assert jaccard({"a", "b", "c"}, {"b", "c", "d"}) == 0.5
    assert jaccard({"a"}, {"a"}) == 1.0
    assert jaccard({"a"}, {"b"}) == 0.0
    assert jaccard(set(), set()) == 0.0


def test_cosine_identical_orthogonal_and_scaled():
    u = {"a": 1.0, "b": 2.0}
    assert math.isclose(cosine(u, u), 1.0)
    assert cosine({"a": 1.0}, {"b": 1.0}) == 0.0
    assert math.isclose(cosine(u, {"a": 2.0, "b": 4.0}), 1.0)
    assert cosine({}, u) == 0.0


def test_cosine_known_value():
    assert math.isclose(cosine({"a": 1.0, "b": 1.0}, {"a": 1.0}), 1 / math.sqrt(2))


def test_idf_rarer_terms_weigh_more():
    idf = idf_table([["a", "b"], ["a", "c"], ["a", "d"]])
    assert idf["b"] > idf["a"]
    assert math.isclose(idf["a"], math.log(4 / 4) + 1.0)


def test_tfidf_repeated_term_sublinear():
    v = tfidf_vec(["x", "x", "x", "y"], {"x": 1.0, "y": 1.0})
    assert math.isclose(v["x"], 1 + math.log(3))
    assert v["y"] == 1.0


def test_tokens_drop_stopwords_and_stem():
    assert tokens("Use this skill to convert the PDFs") == ["convert", "pdf"]


def test_trigger_phrase_extraction():
    d = 'Does X. Use when the user says "Make a PDF" or "export doc". Trigger: foo bar, baz qux.'
    t = trigger_phrases(d)
    assert "make a pdf" in t and "export doc" in t and "foo bar" in t and "baz qux" in t


def test_first_trigger_pos():
    assert first_trigger_pos("Does a thing. Use when asked.") == 14
    assert first_trigger_pos("nothing here") is None


def test_identical_descriptions_collide_with_score_one():
    d = "Convert markdown documents into polished PDF files with table of contents"
    c = find_collisions([S("a", d), S("b", d)], 0.45)
    assert len(c) == 1 and math.isclose(c[0].jaccard, 1.0) and math.isclose(c[0].cosine, 1.0)


def test_unrelated_skills_do_not_collide():
    c = find_collisions([S("a", "Convert markdown documents to PDF files with contents"),
                         S("b", "Review postgres queries for missing indexes and slow joins")], 0.45)
    assert c == []


def test_shared_trigger_forces_report():
    a = S("a", 'Alpha beta gamma delta epsilon. Use when asked to "do the thing".')
    b = S("b", 'Zeta theta iota kappa lambda. Use when asked to "do the thing".')
    c = find_collisions([a, b], 0.9)
    assert len(c) == 1 and c[0].shared_triggers == ["do the thing"]


def test_threshold_filters():
    a = S("a", "convert markdown pdf contents document export")
    b = S("b", "convert markdown pdf slides presentation deck")
    assert find_collisions([a, b], 0.2)
    assert not find_collisions([a, b], 0.95)


def test_same_name_is_skipped_for_collisions():
    d = "Convert markdown documents into polished PDF files"
    assert find_collisions([S("a", d), S("a", d)], 0.1) == []
