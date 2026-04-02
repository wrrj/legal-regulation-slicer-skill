"""元数据推断测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from legal_regulation_slicer.metadata import MetadataOptions, build_document_meta
from legal_regulation_slicer.models import ExtractionError


def test_build_document_meta_maps_three_level_standard_classification(tmp_path: Path) -> None:
    """应将三级标准目录映射为法律分类字段。"""

    input_root = tmp_path / "input"
    file_path = input_root / "法律" / "法律" / "刑法" / "示例办法_20240102.md"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("第一条 为了规范处理。", encoding="utf-8")

    meta = build_document_meta(file_path=file_path, input_root=input_root, options=MetadataOptions())

    assert meta.law_name == "示例办法"
    assert meta.legal_category == "法律"
    assert meta.legal_subcategory == "法律"
    assert meta.legal_topic == "刑法"
    assert meta.status == "未知"
    assert meta.authority_name == "未指定主管机关"


def test_build_document_meta_maps_two_level_standard_classification_and_allows_overrides(tmp_path: Path) -> None:
    """二级标准目录应支持默认映射和 CLI 覆盖。"""

    input_root = tmp_path / "input"
    file_path = input_root / "行政法规" / "行政法规" / "示例规定_20200101.txt"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("第一条 这是示例文本。", encoding="utf-8")

    meta = build_document_meta(
        file_path=file_path,
        input_root=input_root,
        options=MetadataOptions(
            legal_category="行政法规",
            legal_subcategory="行政法规",
            legal_topic="综合",
            authority_default="示例主管部门",
        ),
    )

    assert meta.status == "未知"
    assert meta.authority_name == "示例主管部门"
    assert meta.legal_category == "行政法规"
    assert meta.legal_subcategory == "行政法规"
    assert meta.legal_topic == "综合"


def test_build_document_meta_uses_null_topic_for_two_level_standard_classification(tmp_path: Path) -> None:
    """二级标准目录在未覆盖时应将专题字段设为 null。"""

    input_root = tmp_path / "input"
    file_path = input_root / "行政法规" / "行政法规" / "示例条例_20240101.txt"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("第一条 这是示例文本。", encoding="utf-8")

    meta = build_document_meta(file_path=file_path, input_root=input_root, options=MetadataOptions())

    assert meta.legal_category == "行政法规"
    assert meta.legal_subcategory == "行政法规"
    assert meta.legal_topic is None


def test_build_document_meta_rejects_shallow_classification_path(tmp_path: Path) -> None:
    """少于两级标准分类目录的文件应返回稳定错误码。"""

    input_root = tmp_path / "input"
    file_path = input_root / "示例规定_20200101.txt"
    file_path.parent.mkdir(parents=True)
    file_path.write_text("第一条 这是示例文本。", encoding="utf-8")

    with pytest.raises(ExtractionError) as exc_info:
        build_document_meta(file_path=file_path, input_root=input_root, options=MetadataOptions())

    assert exc_info.value.reason_code == "invalid_classification_path"
