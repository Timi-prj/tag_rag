import time
from typing import List, Tuple, Optional
from tqdm import tqdm
from src.common.types import ParsedBlock
from src.config.manager import ConfigManager
from .text_augmenter import TextAugmenterNode
from .embedding import EmbeddingNode
from .chroma_store import ChromaDBStoreNode


class VectorStorePipeline:
    """向量存储管道：协调文本增强、嵌入生成和存储三个节点（批处理）"""

    def __init__(
        self,
        config: ConfigManager = None,
        augmenter: Optional[TextAugmenterNode] = None,
        embedder: Optional[EmbeddingNode] = None,
        store: Optional[ChromaDBStoreNode] = None,
    ):
        self.config = config or ConfigManager()
        self.augmenter = augmenter or TextAugmenterNode(self.config)
        self.embedder = embedder or EmbeddingNode(self.config)
        self.store = store or ChromaDBStoreNode(self.config)
        self.batch_size = self.config.batch_size

    def process_blocks(
        self,
        blocks: List[ParsedBlock],
        show_progress: bool = True
    ) -> Tuple[int, int, List[str]]:
        """
        处理一批块，返回（成功数，失败数，失败块ID列表）
        """
        if not blocks:
            return 0, 0, []

        total_blocks = len(blocks)
        success_count = 0
        failure_count = 0
        failed_block_ids = []

        # 使用迭代器进行批处理
        iterator = range(0, total_blocks, self.batch_size)
        if show_progress:
            iterator = tqdm(iterator, desc="向量化存储", unit="batch")

        for start_idx in iterator:
            end_idx = min(start_idx + self.batch_size, total_blocks)
            batch = blocks[start_idx:end_idx]

            try:
                # 1. 文本增强
                augmented_pairs = self.augmenter.process(batch)
                batch_blocks, augmented_texts = zip(*augmented_pairs)

                # 2. 嵌入生成
                vectors = self.embedder.process(augmented_texts)

                # 3. 存储到ChromaDB
                self.store.process(vectors, list(batch_blocks))

                success_count += len(batch)
            except Exception as e:
                # 记录失败块
                failure_count += len(batch)
                failed_block_ids.extend([b.block_id for b in batch])
                # 打印错误信息（实际中可以改为日志）
                print(f"批处理失败（起始索引 {start_idx}）: {e}")
                # 继续处理下一批（允许部分失败）

        return success_count, failure_count, failed_block_ids

    def process_single(self, block: ParsedBlock) -> bool:
        """处理单个块，返回是否成功"""
        try:
            # 1. 文本增强
            augmented_text = self.augmenter.augment_batch([block])[0]

            # 2. 嵌入生成
            vector = self.embedder.embed_batch([augmented_text])[0]

            # 3. 存储
            self.store.store_single(vector, block)
            return True
        except Exception as e:
            print(f"块 {block.block_id} 处理失败: {e}")
            return False

    def get_stats(self) -> dict:
        """获取管道统计信息（可扩展）"""
        return {
            "embedding_dimension": self.embedder.get_dimension(),
            "chromadb_collection_count": self.store.get_collection_stats(),
            "batch_size": self.batch_size,
        }
