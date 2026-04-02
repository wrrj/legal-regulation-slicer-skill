"""法条切片规则。"""

from __future__ import annotations

import re

ARTICLE_HEADER_PATTERN = re.compile(
    r"^\s*(第[一二三四五六七八九十百千万零〇两\d]+条(?:之[一二三四五六七八九十百千万零〇两\d]+)?)\s*[　 ]*"
)
STRUCTURE_HEADING_PATTERN = re.compile(
    r"^\s*(?:目\s*录|目录|第[一二三四五六七八九十百千万零〇两\d]+章|第[一二三四五六七八九十百千万零〇两\d]+节)\s*"
)


def split_law_articles(raw_text: str) -> list[tuple[str, str]]:
    """按法条标题切片，并保留下一条出现前的跨行正文。"""

    text = raw_text.strip()
    if not text:
        return []

    chunks: list[tuple[str, str]] = []
    current_article_no: str | None = None
    current_lines: list[str] = []

    for raw_line in text.replace("\r\n", "\n").split("\n"):
        line = raw_line.replace("\u3000", " ").strip()
        if not line:
            continue
        if STRUCTURE_HEADING_PATTERN.match(line):
            continue

        matched = ARTICLE_HEADER_PATTERN.match(line)
        if matched:
            if current_article_no and current_lines:
                chunks.append((current_article_no, "\n".join(current_lines).strip()))

            current_article_no = matched.group(1).strip()
            remain = line[matched.end() :].strip()
            current_lines = [f"{current_article_no} {remain}".strip() if remain else current_article_no]
            continue

        if current_article_no:
            current_lines.append(line)

    if current_article_no and current_lines:
        chunks.append((current_article_no, "\n".join(current_lines).strip()))

    return chunks
