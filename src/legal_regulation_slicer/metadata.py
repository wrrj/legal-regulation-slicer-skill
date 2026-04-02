"""法规元数据与标准记录构建。"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .models import InvalidClassificationPathError, LawDocumentMeta, LegalArticleRecord

LAW_FILE_NAME_DATE_PATTERN = re.compile(r"^(?P<law_name>.+?)_(?P<effective_from>\d{8})$")
UNKNOWN_AUTHORITY = "未指定主管机关"
UNKNOWN_STATUS = "未知"
CHUNK_MODE = "article"
CHUNK_RULE_VERSION = "article_regex_v2"


@dataclass(frozen=True)
class MetadataOptions:
    """CLI 传入的元数据覆盖项。"""

    legal_category: str | None = None
    legal_subcategory: str | None = None
    legal_topic: str | None = None
    authority_default: str | None = None


def build_document_meta(file_path: Path, input_root: Path, options: MetadataOptions) -> LawDocumentMeta:
    """根据文件名、目录上下文和 CLI 覆盖项构建文档元数据。"""

    source_file = build_source_file(file_path, input_root)
    inferred = _infer_classification_from_path(Path(source_file))
    law_name, effective_from = _parse_law_name_and_effective_from(file_path)

    legal_category = options.legal_category or inferred["legal_category"]
    legal_subcategory = options.legal_subcategory or inferred["legal_subcategory"]
    legal_topic = options.legal_topic if options.legal_topic is not None else inferred["legal_topic"]
    if not legal_category or not legal_subcategory:
        raise InvalidClassificationPathError(source_file)
    authority_name = options.authority_default or UNKNOWN_AUTHORITY

    return LawDocumentMeta(
        law_name=law_name,
        authority_name=authority_name,
        legal_category=legal_category,
        legal_subcategory=legal_subcategory,
        legal_topic=legal_topic,
        status=UNKNOWN_STATUS,
        effective_from=effective_from,
        effective_to=None,
        source_file=source_file,
        source_file_type=file_path.suffix.lower().lstrip("."),
        metadata_tags={
            "record_schema_version": "1.0.0",
            "source_name_rule": "filename_date_v1",
            "source_context_rule": "legal_taxonomy_v1",
            "effective_from_source": "file_name_or_mtime",
        },
    )


def build_article_record(meta: LawDocumentMeta, article_no: str, article_text: str) -> LegalArticleRecord:
    """构建法条级标准记录。"""

    law_name_norm = normalize_key_text(meta.law_name)
    article_no_norm = normalize_key_text(article_no)
    content_hash = compute_content_hash(article_text)
    version_id = build_version_id(
        law_name_norm=law_name_norm,
        article_no_norm=article_no_norm,
        effective_from=meta.effective_from,
        content_hash=content_hash,
    )
    embedding_text = " ".join(part for part in [meta.law_name, article_no, article_text] if part).strip()
    metadata_tags = {
        **meta.metadata_tags,
        "version_id": version_id,
        "chunk_mode": CHUNK_MODE,
        "chunk_rule_version": CHUNK_RULE_VERSION,
        "law_name": meta.law_name,
        "law_name_norm": law_name_norm,
        "article_no": article_no,
        "article_no_norm": article_no_norm,
        "content_hash": content_hash,
        "authority_name": meta.authority_name,
        "legal_category": meta.legal_category,
        "legal_subcategory": meta.legal_subcategory,
        "legal_topic": meta.legal_topic or "",
        "status": meta.status,
        "source_file": meta.source_file,
        "source_file_type": meta.source_file_type,
        "effective_from": meta.effective_from.isoformat(),
        "effective_to": "",
        "is_current": "1",
    }

    return LegalArticleRecord(
        chunk_id=version_id,
        version_id=version_id,
        law_name=meta.law_name,
        law_name_norm=law_name_norm,
        article_no=article_no,
        article_no_norm=article_no_norm,
        citation_text=article_text,
        content_hash=content_hash,
        authority_name=meta.authority_name,
        legal_category=meta.legal_category,
        legal_subcategory=meta.legal_subcategory,
        legal_topic=meta.legal_topic,
        status=meta.status,
        effective_from=meta.effective_from,
        effective_to=meta.effective_to,
        is_current=1,
        source_file=meta.source_file,
        source_file_type=meta.source_file_type,
        chunk_mode=CHUNK_MODE,
        chunk_rule_version=CHUNK_RULE_VERSION,
        embedding_text=embedding_text,
        metadata_tags=metadata_tags,
    )


def build_source_file(file_path: Path, input_root: Path) -> str:
    """计算写入结果中的相对来源路径。"""

    resolved_file = file_path.resolve()
    resolved_root = input_root.resolve()
    if resolved_root.is_file():
        return resolved_file.name
    try:
        return resolved_file.relative_to(resolved_root).as_posix()
    except ValueError:
        return resolved_file.name


def normalize_key_text(value: str) -> str:
    """归一化键文本，消除空白差异。"""

    return re.sub(r"\s+", "", value or "").strip().lower()


def compute_content_hash(citation_text: str) -> str:
    """计算法条正文哈希。"""

    return hashlib.sha1(citation_text.strip().encode("utf-8")).hexdigest()


def build_version_id(
    *,
    law_name_norm: str,
    article_no_norm: str,
    effective_from: datetime,
    content_hash: str,
) -> str:
    """生成稳定版本主键。"""

    seed = f"{law_name_norm}|{article_no_norm}|{effective_from.strftime('%Y%m%d')}|{content_hash}"
    return f"v_{hashlib.sha1(seed.encode('utf-8')).hexdigest()}"


def _parse_law_name_and_effective_from(file_path: Path) -> tuple[str, datetime]:
    """从文件名解析法规名称与生效日期。"""

    stem = file_path.stem.strip()
    matched = LAW_FILE_NAME_DATE_PATTERN.match(stem)
    if matched:
        law_name = matched.group("law_name").strip()
        effective_raw = matched.group("effective_from")
        try:
            return law_name, datetime.strptime(effective_raw, "%Y%m%d")
        except ValueError:
            pass
    modified_at = datetime.fromtimestamp(file_path.stat().st_mtime)
    return stem, datetime(modified_at.year, modified_at.month, modified_at.day)


def _infer_classification_from_path(relative_path: Path) -> dict[str, str | None]:
    """从相对路径层级推断标准法律法规分类。"""

    parts = [part.strip() for part in relative_path.parts[:-1] if part and part.strip()]
    return {
        "legal_category": parts[0] if len(parts) >= 1 else None,
        "legal_subcategory": parts[1] if len(parts) >= 2 else None,
        "legal_topic": parts[2] if len(parts) >= 3 else None,
    }
