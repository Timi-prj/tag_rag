import os
import time
from typing import List, Optional
from openai import OpenAI, OpenAIError
from src.config.manager import ConfigManager


class EmbeddingNode:
    """嵌入节点：调用OpenAI兼容API生成文本向量（批处理）"""

    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.client = self._init_client()
        self._dimension = self.config.vector_dim
        self._model = self.config.embedding_model

    def _init_client(self) -> OpenAI:
        """初始化OpenAI客户端（兼容其他OpenAI兼容API）"""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            # 尝试从配置读取
            api_key = self.config.embedding_api_key
        if not api_key:
            raise ValueError("未设置OpenAI API密钥：请设置环境变量 OPENAI_API_KEY 或在配置文件中配置 embedding.api_key")

        base_url = self.config.embedding_api_base
        return OpenAI(api_key=api_key, base_url=base_url)

    def _embed_single(self, text: str, max_retries: int = 3) -> List[float]:
        """生成单个文本的向量"""
        for attempt in range(max_retries):
            try:
                # 构建请求参数
                params = {
                    "model": self._model,
                    "input": text,
                    "encoding_format": "float"
                }
                # 如果配置的维度不是默认值，传递dimensions参数
                # 注意：某些模型可能不支持dimensions参数，但SiliconFlow的API需要
                if self._dimension is not None:
                    params["dimensions"] = self._dimension
                
                response = self.client.embeddings.create(**params)
                embedding = response.data[0].embedding
                # 验证维度
                if len(embedding) != self._dimension:
                    raise ValueError(
                        f"嵌入维度不匹配: 期望 {self._dimension}, 实际 {len(embedding)}"
                    )
                return embedding
            except OpenAIError as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = 2 ** attempt  # 指数退避
                time.sleep(wait_time)
                continue

    def embed_batch(self, texts: List[str], batch_size: Optional[int] = None) -> List[List[float]]:
        """批量生成向量"""
        if batch_size is None:
            batch_size = self.config.batch_size

        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            for text in batch:
                embedding = self._embed_single(text)
                results.append(embedding)
        return results

    def process(self, texts: List[str]) -> List[List[float]]:
        """处理一批文本，返回向量列表"""
        return self.embed_batch(texts)

    def get_dimension(self) -> int:
        """返回嵌入维度"""
        return self._dimension
