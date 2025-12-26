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

    def save_blocks(self, blocks: List[ParsedBlock]):
        """
        待实现：
        1. 遍历 blocks
        2. 调用 OpenAI/HuggingFace 接口将 block.content 转向量
        3. 将 向量 + block.tags 存入 Milvus/Pinecone
        """
        print(f"[Module 2] Placeholder: Received {len(blocks)} blocks to vectorize.")
        for b in blocks[:2]:
            print(f"   -> Would vectorise: {b.block_id} (Tags: {len(b.tags)})")
