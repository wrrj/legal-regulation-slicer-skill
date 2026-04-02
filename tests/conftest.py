"""测试配置：为独立 skill 注入源码路径。"""

from __future__ import annotations

import sys
from pathlib import Path


def _inject_src_path() -> None:
    """将 skill 自身的 src 目录加入导入路径。"""

    skill_root = Path(__file__).resolve().parents[1]
    src_path = skill_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


_inject_src_path()
