from pathlib import Path

from skill_lint.engine import analyze
from skill_lint.model import Options

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"
FIX_PATHS = [FIXTURES / "skills", FIXTURES / "skills-user"]


def mk(base: Path, folder: str, description=None, name="__same__", body="# Body\n", extra_fm="", raw=None):
    """Create base/folder/SKILL.md and return base."""
    d = base / folder
    d.mkdir(parents=True, exist_ok=True)
    if raw is not None:
        (d / "SKILL.md").write_bytes(raw if isinstance(raw, bytes) else raw.encode("utf-8"))
        return base
    nm = folder if name == "__same__" else name
    fm = "---\n"
    if nm is not None:
        fm += f"name: {nm}\n"
    if description is not None:
        fm += f"description: {description}\n"
    fm += extra_fm + "---\n\n"
    (d / "SKILL.md").write_text(fm + body, encoding="utf-8", newline="\n")
    return base


def run(paths, **kw):
    if not isinstance(paths, (list, tuple)):
        paths = [paths]
    return analyze(paths, Options(**kw))


def rules_for(result, folder):
    return {f.rule for f in result.findings if f"/{folder}/" in f.path}


GOOD = 'Fill and flatten PDF forms from JSON data. Use when the user asks to "fill this PDF form" or "flatten a PDF".'
