"""输出文件写入。"""

from __future__ import annotations

import json
from pathlib import Path

from .models import FailedFileRecord, LegalArticleRecord, ManifestSummary


def write_articles_jsonl(output_dir: Path, records: list[LegalArticleRecord]) -> Path:
    """写入法条 JSONL。"""

    path = output_dir / "articles.jsonl"
    lines = [json.dumps(record.to_dict(), ensure_ascii=False) for record in records]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return path


def write_failed_files_jsonl(output_dir: Path, records: list[FailedFileRecord]) -> Path:
    """写入失败文件 JSONL。"""

    path = output_dir / "failed_files.jsonl"
    lines = [json.dumps(record.to_dict(), ensure_ascii=False) for record in records]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return path


def write_manifest(output_dir: Path, manifest: ManifestSummary) -> Path:
    """写入清单 JSON。"""

    path = output_dir / "manifest.json"
    path.write_text(
        json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path
