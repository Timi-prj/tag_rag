import re
from typing import List, Tuple
from src.common.types import Tag

class SpecialChunker:
    """
    特殊切块器：用于处理超长的保护元素（代码块、表格）
    将超长的保护元素拆分为多个适宜向量化的子块
    """
    
    def __init__(self, config):
        self.config = config
    
    def chunk_protected_element(self, 
                               element_type: str, 
                               content: str, 
                               original_tags: List[Tag],
                               max_chars: int = None) -> List[Tuple[str, List[Tag]]]:
        """
        将超长保护元素拆分为多个子块
        
        Args:
            element_type: 'code' 或 'table'
            content: 保护元素的原始文本内容
            original_tags: 原始块的标签列表
            max_chars: 最大字符数（如果为None则使用配置的chunk_max_chars）
            
        Returns:
            List[Tuple[str, List[Tag]]]: 每个子块的（内容, 标签列表）元组列表
        """
        if max_chars is None:
            max_chars = self.config.chunk_max_chars
        
        if element_type == 'code':
            return self._chunk_code(content, original_tags, max_chars)
        elif element_type == 'table':
            return self._chunk_table(content, original_tags, max_chars)
        else:
            # 未知类型，按普通文本切分
            return self._chunk_generic(content, original_tags, max_chars)
    
    def _chunk_code(self, content: str, original_tags: List[Tag], max_chars: int) -> List[Tuple[str, List[Tag]]]:
        """
        切分代码块：尽量按空行或逻辑段落切分
        """
        lines = content.split('\n')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for line in lines:
            line_length = len(line) + 1  # 包括换行符
            
            # 如果当前块不为空且添加该行会超过限制，则结束当前块
            if current_chunk and current_length + line_length > max_chars:
                # 保存当前块
                chunk_text = '\n'.join(current_chunk)
                chunks.append((chunk_text, original_tags.copy()))
                # 开始新块
                current_chunk = [line]
                current_length = line_length
            else:
                current_chunk.append(line)
                current_length += line_length
        
        # 添加最后一个块
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            chunks.append((chunk_text, original_tags.copy()))
        
        # 如果只有一个块且未超过限制，返回原样（不应该发生，因为只有超长才会调用）
        return chunks
    
    def _chunk_table(self, content: str, original_tags: List[Tag], max_chars: int) -> List[Tuple[str, List[Tag]]]:
        """
        切分表格：保持表头（前两行，第二行为Markdown表格分隔符），按行分组切分
        """
        lines = content.split('\n')
        if not lines:
            return []
        
        # 识别表头：Markdown表格前两行（第一行列名，第二行分隔符）
        if len(lines) >= 2:
            header_lines = lines[0:2]  # 前两行作为表头
        else:
            header_lines = lines[0:1]  # 只有一行的情况
        
        # 分割数据行（从第三行开始）
        data_lines = lines[len(header_lines):] if len(lines) > len(header_lines) else []
        
        chunks = []
        current_chunk = header_lines.copy()  # 初始块包含表头
        # 计算当前块长度（包括换行符）
        current_length = sum(len(line) + 1 for line in current_chunk)
        
        for line in data_lines:
            line_length = len(line) + 1
            
            # 如果添加该行会超过限制，且当前块已经包含表头+至少一行数据，则结束当前块
            if current_chunk and current_length + line_length > max_chars and len(current_chunk) > len(header_lines):
                chunk_text = '\n'.join(current_chunk)
                chunks.append((chunk_text, original_tags.copy()))
                # 新块以表头开始，并包含当前行
                current_chunk = header_lines.copy()
                current_chunk.append(line)
                current_length = sum(len(l) + 1 for l in current_chunk)
            else:
                current_chunk.append(line)
                current_length += line_length
        
        # 添加最后一个块
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            chunks.append((chunk_text, original_tags.copy()))
        
        return chunks
    
    def _chunk_generic(self, content: str, original_tags: List[Tag], max_chars: int) -> List[Tuple[str, List[Tag]]]:
        """
        通用切分：按字符长度简单切分
        """
        if len(content) <= max_chars:
            return [(content, original_tags.copy())]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + max_chars
            if end >= len(content):
                chunk = content[start:]
            else:
                # 尽量在换行处截断
                last_newline = content.rfind('\n', start, end)
                if last_newline > start and last_newline - start > max_chars * 0.7:  # 至少保留70%的容量
                    end = last_newline
                else:
                    # 或者在空格处截断
                    last_space = content.rfind(' ', start, end)
                    if last_space > start and last_space - start > max_chars * 0.7:
                        end = last_space
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append((chunk, original_tags.copy()))
            
            start = end if end > start else start + max_chars
        
        return chunks
