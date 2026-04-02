"""数据模型定义。"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


class SkillError(RuntimeError):
    """独立 skill 的基础异常。"""


class ExtractionError(SkillError):
    """文本抽取异常，附带稳定错误码。"""

    def __init__(self, reason_code: str, message: str) -> None:
        """初始化抽取异常。"""

        super().__init__(message)
        self.reason_code = reason_code


class DocPreconversionRequiredError(ExtractionError):
    """`.doc` 文件必须先转换为 `docx`。"""

    def __init__(self, file_name: str) -> None:
        """初始化 `.doc` 预转换异常。"""

        super().__init__(
            "doc_requires_preconversion",
            f"文件 {file_name} 为 .doc 格式，必须先转换为 .docx 后再执行切片。",
        )


class UnsupportedFileTypeError(ExtractionError):
    """不支持的文件格式异常。"""

    def __init__(self, suffix: str) -> None:
        """初始化不支持格式异常。"""

        display_suffix = suffix or "<no-suffix>"
        super().__init__("unsupported_file_type", f"暂不支持的文件类型：{display_suffix}")


class EmptyExtractionError(ExtractionError):
    """抽取后为空的异常。"""

    def __init__(self, file_name: str) -> None:
        """初始化空文本异常。"""

        super().__init__("empty_extracted_text", f"文件 {file_name} 未抽取到可用文本。")


class InvalidClassificationPathError(ExtractionError):
    """分类目录结构不满足入库要求。"""

    def __init__(self, source_file: str) -> None:
        """初始化分类目录结构异常。"""

        super().__init__(
            "invalid_classification_path",
            f"文件 {source_file} 不在至少两级的标准法律法规分类目录下，无法推断分类字段。",
        )


@dataclass(frozen=True)
class LawDocumentMeta:
    """法规文档级元数据。"""

    law_name: str
    authority_name: str
    legal_category: str
    legal_subcategory: str
    legal_topic: str | None
    status: str
    effective_from: datetime
    effective_to: datetime | None
    source_file: str
    source_file_type: str
    metadata_tags: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class LegalArticleRecord:
    """法条级标准输出记录。"""

    chunk_id: str
    version_id: str
    law_name: str
    law_name_norm: str
    article_no: str
    article_no_norm: str
    citation_text: str
    content_hash: str
    authority_name: str
    legal_category: str
    legal_subcategory: str
    legal_topic: str | None
    status: str
    effective_from: datetime
    effective_to: datetime | None
    is_current: int
    source_file: str
    source_file_type: str
    chunk_mode: str
    chunk_rule_version: str
    embedding_text: str
    metadata_tags: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为可直接写入 JSON 的字典。"""

        payload = asdict(self)
        payload["effective_from"] = self.effective_from.isoformat()
        payload["effective_to"] = self.effective_to.isoformat() if self.effective_to else None
        return payload


@dataclass(frozen=True)
class FailedFileRecord:
    """失败文件记录。"""

    source_file: str
    source_file_type: str
    reason_code: str
    reason_message: str

    def to_dict(self) -> dict[str, str]:
        """转换为 JSON 可写入字典。"""

        return asdict(self)


@dataclass(frozen=True)
class ManifestSummary:
    """输出清单摘要。"""

    input_path: str
    output_path: str
    generated_at: str
    recursive: bool
    candidate_files: int
    processed_files: int
    failed_files: int
    article_count: int
    failed_reasons: dict[str, int] = field(default_factory=dict)
    cli_args: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为 JSON 可写入字典。"""

        return asdict(self)
