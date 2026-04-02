"""切片规则测试。"""

from __future__ import annotations

from legal_regulation_slicer.splitter import split_law_articles


def test_split_law_articles_handles_articles_subarticles_and_multiline_content() -> None:
    """应按法条与法条之分片，并保留条文跨行内容。"""

    raw_text = """
    目录
    第一章 总则
    第一条 为了规范处理。
    本办法适用于示例场景。

    第二条之一 有特别规定的，从其规定。
    第二章 附则
    第三条 本办法自公布之日起施行。
    """

    articles = split_law_articles(raw_text)

    assert articles == [
        ("第一条", "第一条 为了规范处理。\n本办法适用于示例场景。"),
        ("第二条之一", "第二条之一 有特别规定的，从其规定。"),
        ("第三条", "第三条 本办法自公布之日起施行。"),
    ]


def test_split_law_articles_returns_empty_for_blank_text() -> None:
    """空文本不应产生任何法条切片。"""

    assert split_law_articles(" \n\t ") == []
