from typing import List
from src.config.manager import ConfigManager
from src.common.types import ParsedBlock
from src.modules.vector_store.nodes.pipeline import VectorStorePipeline


class VectorStoreConnector:
    """
    模块二：向量存储连接器
    职责：接收 ParsedBlock -> 文本增强 -> Embedding -> 存储到ChromaDB
    """
    def __init__(self):
        self.config = ConfigManager()
        self.pipeline = None
        self._initialize_pipeline()
        print(f"[Module 2] Initialized Vector Store with dim={self.config.vector_dim}")

    def _initialize_pipeline(self):
        """初始化向量存储管道"""
        try:
            self.pipeline = VectorStorePipeline(self.config)
        except Exception as e:
            print(f"[Module 2] 警告：管道初始化失败，将使用占位模式: {e}")
            self.pipeline = None

    def save_blocks(self, blocks: List[ParsedBlock]):
        """
        实现：
        1. 使用管道处理块（文本增强 -> 嵌入 -> 存储）
        2. 如果管道不可用，则回退到占位模式
        """
        if not blocks:
            print("[Module 2] 无块需要向量化")
            return

        # 如果管道可用，使用管道处理
        if self.pipeline:
            print(f"[Module 2] 开始向量化 {len(blocks)} 个块...")
            success, failure, failed_ids = self.pipeline.process_blocks(blocks, show_progress=True)
            print(f"[Module 2] 向量化完成: {success} 成功, {failure} 失败")
            if failure > 0:
                print(f"[Module 2] 失败的块ID（前10个）: {failed_ids[:10]}")
            
            # 显示前两个块的增强文本（调试信息）
            for b in blocks[:2]:
                augmented = self.pipeline.augmenter.augment_batch([b])[0]
                print(f"   -> Block {b.block_id}:")
                print(f"      Original content: {b.content[:100]}..." if len(b.content) > 100 else f"      Original content: {b.content}")
                print(f"      Augmented text: {augmented[:150]}..." if len(augmented) > 150 else f"      Augmented text: {augmented}")
                print(f"      Tags: {len(b.tags)}")
                if b.protected_element_type:
                    print(f"      Protected element type: {b.protected_element_type}")
        else:
            # 管道不可用，使用占位模式
            print(f"[Module 2] Placeholder: Received {len(blocks)} blocks to vectorize.")
            for b in blocks[:2]:
                # 使用旧的增强文本逻辑
                if b.protected_element_type is not None:
                    augmented = b.content
                else:
                    tag_strs = [f"{tag.key}: {tag.value}" for tag in b.tags]
                    parts = []
                    if tag_strs:
                        parts.extend(tag_strs)
                    parts.append(b.content)
                    augmented = " ".join(parts)
                
                print(f"   -> Block {b.block_id}:")
                print(f"      Original content: {b.content[:100]}..." if len(b.content) > 100 else f"      Original content: {b.content}")
                print(f"      Augmented text: {augmented[:150]}..." if len(augmented) > 150 else f"      Augmented text: {augmented}")
                print(f"      Tags: {len(b.tags)}")
                if b.protected_element_type:
                    print(f"      Protected element type: {b.protected_element_type}")
