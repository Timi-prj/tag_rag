import re
from typing import List, Optional
from src.config.manager import ConfigManager
from src.common.types import Tag

class TagExtractorNode:
    """节点功能：标签提取与清洗"""
    
    def __init__(self, config: ConfigManager):
        self.config = config

    def extract_from_text(self, text: str, scope_level: int) -> Optional[Tag]:
        """从文本中解析标签，如果被过滤则返回 None"""
        if not text.strip().startswith("#"):
            return None
            
        raw = text.strip()
        content = raw[1:] # 去掉 #
        
        # 1. 检查排除规则
        for pattern in self.config.exclude_patterns:
            if pattern.match(raw):
                return None

        # 2. 解析 Key/Value
        # 逻辑：如果是 "?city/beijing", key=city, value=beijing (seed tag)
        # 逻辑：如果是 "python", key=tag, value=python
        
        if content.startswith(self.config.tag_prefix):
            # 种子标签逻辑
            real_content = content[len(self.config.tag_prefix):]
            parts = real_content.split('/', 1)
            key = parts[0]
            value = parts[1] if len(parts) > 1 else "true"
        else:
            # 普通标签
            parts = content.split('/', 1)
            key = parts[0] if len(parts) > 1 else "topic"
            value = parts[1] if len(parts) > 1 else parts[0]

        return Tag(key=key, value=value, original_text=raw, scope_level=scope_level)
