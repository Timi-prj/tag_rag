import re
from dataclasses import dataclass

@dataclass
class Row:
    index: int
    text: str
    clean_text: str
    is_header: bool = False
    header_level: int = 0
    is_tag: bool = False
    is_code_fence: bool = False

class RowParserNode:
    """节点功能：单行文本解析"""
    
    RE_HEADER = re.compile(r'^(#{1,6})\s+(.*)')
    RE_TAG = re.compile(r'^\s*(#[^#\s]+)\s*$') # 简单标签匹配
    RE_FENCE = re.compile(r'^\s*(`{3,}|~{3,})')

    def process(self, raw_lines: list[str]) -> list[Row]:
        result = []
        for idx, line in enumerate(raw_lines):
            clean = line.strip()
            row = Row(index=idx, text=line, clean_text=clean)
            
            # 识别 Code Fence
            if self.RE_FENCE.match(line):
                row.is_code_fence = True
                result.append(row)
                continue

            # 识别 Header
            h_match = self.RE_HEADER.match(clean)
            if h_match:
                row.is_header = True
                row.header_level = len(h_match.group(1))
                row.clean_text = h_match.group(2).strip()
                result.append(row)
                continue

            # 识别 独占一行的Tag
            if self.RE_TAG.match(clean):
                row.is_tag = True
            
            result.append(row)
        return result
