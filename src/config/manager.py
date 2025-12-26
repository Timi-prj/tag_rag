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
        self.output_dir = p_conf.get('output_dir', './output')
        self.chunk_max_chars = p_conf.get('chunk_strategy', {}).get('max_chars', 1000)
        self.chunk_overlap = p_conf.get('chunk_strategy', {}).get('overlap_rows', 2)

        # 标签配置
        t_conf = self._raw.get('tags', {})
        self.tag_prefix = t_conf.get('prefix', '?')
        self.exclude_patterns: List[Pattern] = [
            re.compile(p) for p in t_conf.get('exclude_regex', [])
        ]

        # 模块二配置 (预留)
        v_conf = self._raw.get('vector_store', {})
        self.vector_dim = v_conf.get('dimension', 1536)
