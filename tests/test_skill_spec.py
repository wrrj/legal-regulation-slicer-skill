"""Skill 文档规范回归测试。"""

from __future__ import annotations

import re
from pathlib import Path


def _skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _skill_text() -> str:
    return (_skill_root() / "SKILL.md").read_text(encoding="utf-8")


def test_skill_has_valid_frontmatter() -> None:
    """SKILL.md 应包含 Agent Skills 所需的最小 frontmatter。"""

    text = _skill_text()
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert match, "SKILL.md must start with YAML frontmatter."

    frontmatter = match.group(1)
    name_match = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
    description_match = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
    assert name_match, "Frontmatter must define a name."
    assert description_match, "Frontmatter must define a description."

    name = name_match.group(1).strip()
    description = description_match.group(1).strip()

    assert name == _skill_root().name
    assert re.fullmatch(r"[a-z0-9-]+", name)
    assert len(name) <= 64
    assert description
    assert len(description) <= 1024


def test_skill_links_point_to_existing_files() -> None:
    """SKILL.md 中的相对链接应指向仓库内现有文件。"""

    skill_root = _skill_root()
    link_targets = re.findall(r"\[[^\]]+\]\(([^)#]+)\)", _skill_text())

    assert link_targets, "SKILL.md should include project file links for progressive disclosure."
    for target in link_targets:
        assert not target.startswith(("http://", "https://"))
        assert (skill_root / target).exists(), f"Missing linked file: {target}"


def test_readme_stays_aligned_with_skill_contract() -> None:
    """README 应保留与 SKILL 一致的核心接口与验证说明。"""

    readme_text = (_skill_root() / "README.md").read_text(encoding="utf-8")
    skill_text = _skill_text()

    assert "articles.jsonl" in readme_text
    assert "manifest.json" in readme_text
    assert "failed_files.jsonl" in readme_text
    assert "python scripts/slice_regulations.py --help" in readme_text
    assert "$env:PYTHONUTF8 = \"1\"" in readme_text
    for field_name in ("legal_category", "legal_subcategory", "legal_topic"):
        assert field_name in readme_text
        assert field_name in skill_text
    for old_field_name in ("law_domain", "source_category", "source_region"):
        assert old_field_name not in readme_text
        assert old_field_name not in skill_text
