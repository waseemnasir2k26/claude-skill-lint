from skill_lint.parse import parse_skill_text


def test_plain_and_quoted_scalars():
    p = parse_skill_text('---\nname: a-b\ndescription: "Say \\"hi\\": now"\n---\nbody')
    assert p.present
    assert p.data["name"] == "a-b"
    assert p.data["description"] == 'Say "hi": now'
    assert p.body == "body"


def test_single_quote_escape():
    p = parse_skill_text("---\ndescription: 'it''s fine'\n---\n")
    assert p.data["description"] == "it's fine"


def test_literal_block_scalar_keeps_newlines():
    p = parse_skill_text("---\nname: x\ndescription: |\n  line one\n  line two\n---\nB")
    assert p.data["description"] == "line one\nline two"


def test_folded_block_scalar_joins_lines():
    p = parse_skill_text("---\ndescription: >\n  line one\n  line two\n\n  para two\n---\nB")
    assert p.data["description"] == "line one line two\npara two"


def test_plain_multiline_continuation():
    p = parse_skill_text("---\ndescription: first part\n  second part\nname: x\n---\n")
    assert p.data["description"] == "first part second part"
    assert p.data["name"] == "x"


def test_lists_and_nested_mapping():
    p = parse_skill_text("---\nname: x\ntools:\n  - Read\n  - Bash\nmetadata:\n  author: me\n  version: 2\nallowed: [a, b]\n---\n")
    assert p.data["tools"] == ["Read", "Bash"]
    assert p.data["metadata"] == {"author": "me", "version": "2"}
    assert p.data["allowed"] == ["a", "b"]


def test_key_lines_are_one_based_file_lines():
    p = parse_skill_text("---\nname: x\ndescription: y\n---\n")
    assert p.key_lines == {"name": 2, "description": 3}


def test_unterminated_frontmatter_is_error():
    p = parse_skill_text("---\nname: x\nno end")
    assert p.present and p.errors and "never closed" in p.errors[0]


def test_no_frontmatter():
    p = parse_skill_text("# just markdown\n")
    assert not p.present and p.data == {}


def test_crlf_and_bom_are_handled():
    p = parse_skill_text("﻿---\r\nname: x\r\ndescription: y z\r\n---\r\nbody\r\n")
    assert p.present and p.data["name"] == "x" and p.data["description"] == "y z"
    assert "\r" not in p.body


def test_plain_colon_detected():
    p = parse_skill_text("---\ndescription: Does a thing: really\n---\n")
    assert "description" in p.plain_colon


def test_trailing_comment_stripped_from_plain():
    p = parse_skill_text("---\nname: x # comment\n---\n")
    assert p.data["name"] == "x"


def test_garbage_line_reported_not_raised():
    p = parse_skill_text("---\nname: x\nthis is not yaml\n---\n")
    assert p.errors
