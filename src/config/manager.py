import yaml
import os
import re
from typing import List, Pattern

class ConfigManager:
    _instance = None

    def __new__(cls, config_path: str = "config.yaml"):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config(config_path)
        return cls._instance

    def _load_config(self, path: str):
        if not os.path.exists(path):
            # Docker 容器内路径回退逻辑
            path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.yaml")
        
        with open(path, 'r', encoding='utf-8') as f:
            self._raw = yaml.safe_load(f)

        # 模块一配置
        p_conf = self._raw.get('parser', {})
        self.input_dir = p_conf.get('input_dir', './data')
        self.output_dir = p_conf.get('output_dir', './output')
        self.file_extensions = p_conf.get('file_extensions', ['.md', '.markdown'])
        self.chunk_max_chars = p_conf.get('chunk_strategy', {}).get('max_chars', 1000)
        self.chunk_overlap = p_conf.get('chunk_strategy', {}).get('overlap_rows', 2)

        # 标签配置
        t_conf = self._raw.get('tags', {})
        self.tag_prefix = t_conf.get('prefix', '?')
        self.exclude_patterns: List[Pattern] = [
            re.compile(p) for p in t_conf.get('exclude_regex', [])
        ]

        # 模块二配置
        v_conf = self._raw.get('vector_store', {})
        self.vector_dim = v_conf.get('dimension', 1536)
        self.vector_store_provider = v_conf.get('provider', 'chromadb')
        self.batch_size = v_conf.get('batch_size', 32)
        
        # 嵌入配置
        embedding_conf = v_conf.get('embedding', {})
        self.embedding_api_base = embedding_conf.get('api_base', 'https://api.openai.com/v1')
        self.embedding_model = embedding_conf.get('model', 'text-embedding-3-small')
        self.embedding_api_key = embedding_conf.get('api_key', '')
        
        # 速率限制配置
        rate_limit_conf = embedding_conf.get('rate_limit', {})
        self.embedding_rpm = rate_limit_conf.get('rpm', 10)
        self.embedding_tpm = rate_limit_conf.get('tpm', 10000)
        self.embedding_enable_adaptive_delay = rate_limit_conf.get('enable_adaptive_delay', True)
        self.embedding_request_delay = rate_limit_conf.get('request_delay', 0.5)
        
        # ChromaDB配置
        chroma_conf = v_conf.get('chromadb', {})
        self.chroma_persist_directory = chroma_conf.get('persist_directory', './chroma_db')
        self.chroma_collection_name = chroma_conf.get('collection_name', 'tag_rag_vectors')

        # 日志配置
        log_conf = self._raw.get('logging', {})
        self.log_level = log_conf.get('level', 'INFO')
        self.log_format = log_conf.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.log_handlers = log_conf.get('handlers', {})
