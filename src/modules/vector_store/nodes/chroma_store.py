import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any
from src.common.types import ParsedBlock, Tag
from src.config.manager import ConfigManager


class ChromaDBStoreNode:
    """ChromaDB存储节点：将向量和元数据存储到ChromaDB（批处理）"""

    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.client = None
        self.collection = None
        self._initialize()

    def _initialize(self):
        """初始化ChromaDB客户端和集合"""
        persist_directory = self.config.chroma_persist_directory
        collection_name = self.config.chroma_collection_name

        # 创建客户端（持久化到磁盘）
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        # 获取或创建集合
        try:
            self.collection = self.client.get_collection(collection_name)
        except (ValueError, chromadb.errors.NotFoundError):
            # 集合不存在，创建新集合
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}  # 默认使用余弦相似度
            )

    def _prepare_metadata(self, block: ParsedBlock) -> Dict[str, Any]:
        """准备块的元数据"""
        metadata = {
            "block_id": block.block_id,
            "start_line": block.start_line,
            "end_line": block.end_line,
            "is_splited": block.is_splited,
            "protected_element_type": block.protected_element_type or "",
            "protected_element_overlength": block.protected_element_overlength,
        }

        # 添加标签
        for tag in block.tags:
            metadata[f"tag_{tag.key}"] = tag.value

        return metadata

    def store_single(self, vector: List[float], block: ParsedBlock):
        """存储单个向量和元数据"""
        metadata = self._prepare_metadata(block)
        self.collection.add(
            embeddings=[vector],
            metadatas=[metadata],
            ids=[block.block_id],
            documents=[block.content]  # 可选：存储原始文本
        )

    def store_batch(
        self,
        vectors: List[List[float]],
        blocks: List[ParsedBlock],
        batch_size: int = 100
    ):
        """批量存储向量和元数据"""
        for i in range(0, len(vectors), batch_size):
            batch_vectors = vectors[i:i + batch_size]
            batch_blocks = blocks[i:i + batch_size]

            ids = [block.block_id for block in batch_blocks]
            metadatas = [self._prepare_metadata(block) for block in batch_blocks]
            documents = [block.content for block in batch_blocks]

            self.collection.add(
                embeddings=batch_vectors,
                metadatas=metadatas,
                ids=ids,
                documents=documents
            )

    def process(self, vectors: List[List[float]], blocks: List[ParsedBlock]):
        """处理一批向量和块，存储到ChromaDB"""
        self.store_batch(vectors, blocks)

    def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        return self.collection.count()
