"""独立法规切片 CLI。"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = SKILL_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from legal_regulation_slicer.extractors import ExtractionError, discover_candidate_files, extract_text_from_file
from legal_regulation_slicer.metadata import MetadataOptions, build_article_record, build_document_meta, build_source_file
from legal_regulation_slicer.models import FailedFileRecord, ManifestSummary
from legal_regulation_slicer.splitter import split_law_articles
from legal_regulation_slicer.writer import write_articles_jsonl, write_failed_files_jsonl, write_manifest


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""

    parser = argparse.ArgumentParser(description="将法律法规文件切分为法条级 JSONL 记录。")
    parser.add_argument("--input", required=True, help="输入文件或目录路径")
    parser.add_argument("--output", required=True, help="输出目录路径")
    parser.add_argument("--recursive", action="store_true", help="递归扫描输入目录")
    parser.add_argument("--legal-category", default="", help="覆盖默认一级法律分类")
    parser.add_argument("--legal-subcategory", default="", help="覆盖默认二级法律分类")
    parser.add_argument("--legal-topic", default="", help="覆盖默认三级法律专题分类")
    parser.add_argument("--authority-default", default="", help="覆盖默认主管机关")
    return parser


def main(argv: list[str] | None = None) -> int:
    """执行法规切片主流程。"""

    parser = build_parser()
    args = parser.parse_args(argv)

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    if not input_path.exists():
        parser.error(f"输入路径不存在：{input_path}")

    output_path.mkdir(parents=True, exist_ok=True)
    metadata_options = MetadataOptions(
        legal_category=args.legal_category.strip() or None,
        legal_subcategory=args.legal_subcategory.strip() or None,
        legal_topic=args.legal_topic.strip() or None,
        authority_default=args.authority_default.strip() or None,
    )

    candidate_files = discover_candidate_files(input_path, recursive=args.recursive)
    input_root = input_path if input_path.is_dir() else input_path.parent
    failed_reason_counter: Counter[str] = Counter()
    articles = []
    failures: list[FailedFileRecord] = []
    processed_files = 0

    for file_path in candidate_files:
        try:
            raw_text = extract_text_from_file(file_path)
            article_slices = split_law_articles(raw_text)
            if not article_slices:
                raise ExtractionError("no_article_detected", f"文件 {file_path.name} 未识别到任何法条标题。")

            document_meta = build_document_meta(file_path=file_path, input_root=input_root, options=metadata_options)
            for article_no, article_text in article_slices:
                articles.append(build_article_record(document_meta, article_no, article_text))
            processed_files += 1
        except ExtractionError as exc:
            failures.append(
                FailedFileRecord(
                    source_file=build_source_file(file_path, input_root),
                    source_file_type=file_path.suffix.lower().lstrip("."),
                    reason_code=exc.reason_code,
                    reason_message=str(exc),
                )
            )
            failed_reason_counter[exc.reason_code] += 1
        except Exception as exc:  # pragma: no cover - 兜底保护，仅用于 CLI 失败清单。
            failures.append(
                FailedFileRecord(
                    source_file=build_source_file(file_path, input_root),
                    source_file_type=file_path.suffix.lower().lstrip("."),
                    reason_code="unexpected_error",
                    reason_message=str(exc),
                )
            )
            failed_reason_counter["unexpected_error"] += 1

    articles.sort(key=lambda item: (item.source_file, item.law_name, item.article_no, item.version_id))
    failures.sort(key=lambda item: (item.source_file, item.reason_code))

    write_articles_jsonl(output_path, articles)
    write_failed_files_jsonl(output_path, failures)
    manifest = ManifestSummary(
        input_path=str(input_path),
        output_path=str(output_path),
        generated_at=datetime.now(timezone.utc).isoformat(),
        recursive=bool(args.recursive),
        candidate_files=len(candidate_files),
        processed_files=processed_files,
        failed_files=len(failures),
        article_count=len(articles),
        failed_reasons=dict(sorted(failed_reason_counter.items())),
        cli_args={
            "legal_category": metadata_options.legal_category or "",
            "legal_subcategory": metadata_options.legal_subcategory or "",
            "legal_topic": metadata_options.legal_topic or "",
            "authority_default": metadata_options.authority_default or "",
        },
    )
    write_manifest(output_path, manifest)

    summary = {
        "candidate_files": len(candidate_files),
        "processed_files": processed_files,
        "failed_files": len(failures),
        "article_count": len(articles),
        "output_dir": str(output_path),
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
