from typing import List
from src.config.manager import ConfigManager
from src.common.types import ParsedBlock

class VectorStoreConnector:
    """
    模块二：向量存储连接器 (占位)
    职责：接收 ParsedBlock -> Embedding -> Store
    """
    def __init__(self):
        self.config = ConfigManager()
        print(f"[Module 2] Initialized Vector Store with dim={self.config.vector_dim}")

    def _build_augmented_text(self, block: ParsedBlock) -> str:
        """构建增强文本：将标签转换为 key: value 格式并拼接在内容前"""
        if block.protected_element_type is not None:
            # 保护元素块不增强
            return block.content
        tag_strs = [f"{tag.key}: {tag.value}" for tag in block.tags]
        parts = []
        if tag_strs:
            parts.extend(tag_strs)
        parts.append(block.content)
        return " ".join(parts)

    def save_blocks(self, blocks: List[ParsedBlock]):
        """
        待实现：
        1. 遍历 blocks
        2. 调用 OpenAI/HuggingFace 接口将 block.content 转向量
        3. 将 向量 + block.tags 存入 Milvus/Pinecone
        """
        print(f"[Module 2] Placeholder: Received {len(blocks)} blocks to vectorize.")
        for b in blocks[:2]:
            augmented = self._build_augmented_text(b)
            print(f"   -> Block {b.block_id}:")
            print(f"      Original content: {b.content[:100]}..." if len(b.content) > 100 else f"      Original content: {b.content}")
            print(f"      Augmented text: {augmented[:150]}..." if len(augmented) > 150 else f"      Augmented text: {augmented}")
            print(f"      Tags: {len(b.tags)}")
            if b.protected_element_type:
                print(f"      Protected element type: {b.protected_element_type}")
