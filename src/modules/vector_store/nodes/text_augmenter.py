from typing import List, Tuple
from src.common.types import ParsedBlock
from src.config.manager import ConfigManager


class TextAugmenterNode:
    """文本增强节点：将标签转换为 key: value 格式并拼接在内容前（批处理）"""

    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()

    def _augment_single(self, block: ParsedBlock) -> str:
        """增强单个块的文本"""
        if block.protected_element_type is not None:
            # 保护元素块不增强
            return block.content
        tag_strs = [f"{tag.key}: {tag.value}" for tag in block.tags]
        parts = []
        if tag_strs:
            parts.extend(tag_strs)
        parts.append(block.content)
        return " ".join(parts)

    def augment_batch(self, blocks: List[ParsedBlock]) -> List[str]:
        """批量增强文本"""
        return [self._augment_single(block) for block in blocks]

    def process(self, blocks: List[ParsedBlock]) -> List[Tuple[ParsedBlock, str]]:
        """处理一批块，返回(块, 增强文本)的列表"""
        augmented_texts = self.augment_batch(blocks)
        return list(zip(blocks, augmented_texts))
