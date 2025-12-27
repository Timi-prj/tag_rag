from dataclasses import dataclass, field
from typing import List, Optional, Dict

@dataclass
class Tag:
    """标签定义"""
    key: str
    value: str
    original_text: str

@dataclass
class ParsedBlock:
    """
    这是模块一的产物，也是模块二的输入。
    包含原文片段和解析出的元数据。
    """
    block_id: str       # 唯一ID
    content: str        # 待向量化的文本
    start_line: int
    end_line: int
    tags: List[Tag]     # 元数据
    is_splited: bool = False  # 新增：是否被切分
    protected_element_type: Optional[str] = None  # 新增：保护元素类型（'code', 'table'）
    protected_element_overlength: bool = False  # 新增：保护元素本身是否超长
