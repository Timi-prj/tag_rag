import re
from typing import List, Optional
from src.config.manager import ConfigManager
from src.common.types import Tag

class TagExtractorNode:
    """节点功能：标签提取与清洗"""
    
    def __init__(self, config: ConfigManager):
        self.config = config

    def extract_from_text(self, text: str) -> Optional[Tag]:
        """从文本中解析标签，如果被过滤则返回 None"""
        if not text.strip().startswith("#"):
            return None
            
        raw = text.strip()
        
        # 处理种子标签：将 #?xxx/yyy 转换为 #seed/xxx/yyy
        if raw.startswith(f"#{self.config.tag_prefix}"):
            # 转换：去掉#?，加上#seed/，确保有斜杠分隔符
            seed_content = raw[2:]  # 去掉 "#?"
            raw = f"#seed/{seed_content}"
        
        content = raw[1:]  # 去掉 #
        
        # 1. 检查排除规则（使用转换后的raw）
        for pattern in self.config.exclude_patterns:
            if pattern.match(raw):
                return None

        # 2. 解析 Key/Value
        parts = content.split('/', 1)
        key = parts[0] if len(parts) > 1 else "topic"
        value = parts[1] if len(parts) > 1 else parts[0]

        return Tag(key=key, value=value, original_text=raw)
