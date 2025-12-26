from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class Tag:
    """标签定义"""
    key: str
    value: str
    original_text: str
    scope_level: int  # 0=全文, 1=H1, 2=H2...

@dataclass
class ParsedBlock:
    """
    这是模块一的产物，也是模块二的输入。
    包含原文片段和解析出的元数据。
    """
    file_path: str
    block_id: str       # 唯一ID
    content: str        # 待向量化的文本
    start_line: int
    end_line: int
    tags: List[Tag]     # 元数据
    header_path: str    # 如 "一级标题 > 二级标题"
