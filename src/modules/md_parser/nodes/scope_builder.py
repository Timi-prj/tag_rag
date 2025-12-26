from typing import List
import hashlib
from src.common.types import ParsedBlock, Tag
from src.modules.md_parser.nodes.row_parser import Row
from src.modules.md_parser.nodes.tag_extractor import TagExtractorNode

class ScopeBuilderNode:
    """节点功能：维护文档结构作用域，生成最终块"""
    
    def __init__(self, config, tag_node: TagExtractorNode):
        self.config = config
        self.tag_node = tag_node

    def run(self, rows: List[Row], file_path: str) -> List[ParsedBlock]:
        blocks = []
        
        # 状态寄存器
        current_buffer: List[Row] = []
        heading_stack: List[str] = []
        # 作用域标签：scope_tags[1] 存储属于一级标题下的标签
        scope_tags: dict[int, List[Tag]] = {i: [] for i in range(10)}
        
        for row in rows:
            # 1. 如果是标题，触发切分
            if row.is_header:
                if current_buffer:
                    b = self._flush_block(current_buffer, heading_stack, scope_tags, file_path)
                    if b: blocks.append(b)
                
                # 更新标题栈
                lvl = row.header_level
                # 清除比当前级别更深的作用域标签
                for i in range(lvl, 10): scope_tags[i] = []
                
                # 更新标题路径
                if lvl > len(heading_stack):
                    heading_stack.append(row.clean_text)
                else:
                    heading_stack = heading_stack[:lvl-1]
                    heading_stack.append(row.clean_text)
                
                # 标题行本身也加入下一个块
                current_buffer = [row]
                continue

            # 2. 如果是标签行
            if row.is_tag:
                tag = self.tag_node.extract_from_text(row.clean_text, len(heading_stack))
                if tag:
                    # 将标签加入当前最深层级的作用域
                    current_lvl = len(heading_stack)
                    # 如果当前还在根节点(无标题)，lvl=0
                    if current_lvl == 0: current_lvl = 0 
                    scope_tags[current_lvl].append(tag)
                # 标签行不放入正文 Buffer
                continue

            # 3. 普通内容
            current_buffer.append(row)
            
            # 4. 检查是否超长 (简单切分，暂不处理复杂重叠)
            current_len = sum(len(r.text) for r in current_buffer)
            if current_len > self.config.chunk_max_chars:
                b = self._flush_block(current_buffer, heading_stack, scope_tags, file_path)
                if b: blocks.append(b)
                # 保留重叠行
                overlap = self.config.chunk_overlap
                current_buffer = current_buffer[-overlap:] if overlap > 0 else []

        # 收尾
        if current_buffer:
            b = self._flush_block(current_buffer, heading_stack, scope_tags, file_path)
            if b: blocks.append(b)
            
        return blocks

    def _flush_block(self, rows: List[Row], headings: List[str], scopes: dict, fpath: str) -> ParsedBlock:
        text = "".join(r.text for r in rows).strip()
        if not text: return None

        # 收集所有当前有效的标签 (继承逻辑)
        active_tags = []
        # 从0级(全文)到当前级别
        current_lvl = len(headings)
        for i in range(0, current_lvl + 1):
            if i in scopes:
                active_tags.extend(scopes[i])

        # 生成ID
        bid = hashlib.md5(f"{fpath}_{rows[0].index}_{text[:20]}".encode()).hexdigest()

        return ParsedBlock(
            file_path=fpath,
            block_id=bid,
            content=text,
            start_line=rows[0].index,
            end_line=rows[-1].index,
            tags=active_tags, # 浅拷贝建议
            header_path="/".join(headings)
        )
