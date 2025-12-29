import hashlib
from typing import List, Optional
from src.common.types import ParsedBlock, Tag
from src.modules.md_parser.nodes.row_parser import Row
from src.modules.md_parser.nodes.tag_extractor import TagExtractorNode
from src.modules.md_parser.nodes.parsing_context import ParsingContext
from src.modules.md_parser.nodes.special_chunker import SpecialChunker


class ScopeBuilderNode:
    """节点功能：使用上下文状态机维护文档结构，生成最终块，实现保护元素优先切块策略"""

    def __init__(self, config, tag_node: TagExtractorNode):
        self.config = config
        self.tag_node = tag_node
        self.special_chunker = SpecialChunker(config)

    def _should_discard_block(self, text: str) -> bool:
        """
        判断是否应舍弃该块：内容仅包含标题行（以1-6个#开头，后跟空格和文本）
        且无其他实质性内容。
        """
        lines = text.strip().splitlines()
        if not lines:
            return True  # 空内容
        # 检查每一行是否都是标题行（允许前后有空行，但已strip）
        for line in lines:
            stripped = line.strip()
            # 标题行模式：以1-6个#开头，后跟至少一个空格，然后有非空文本
            if not (stripped.startswith('#') and ' ' in stripped):
                return False  # 非标题行，保留块
            # 验证#数量在1-6之间（标题级别）
            hash_count = 0
            for char in stripped:
                if char == '#':
                    hash_count += 1
                else:
                    break
            if hash_count < 1 or hash_count > 6 or stripped[hash_count] != ' ':
                return False  # 不符合标题格式，保留块
        # 所有行都是标题行，舍弃
        return True

    def run(self, rows: List[Row], file_path: str) -> List[ParsedBlock]:
        blocks = []
        context = ParsingContext()

        i = 0
        while i < len(rows):
            row = rows[i]

            # 1. 如果是标题，触发切分（包括当前缓冲区中的保护元素）
            if row.is_header:
                # 先切分当前缓冲区（如果有内容）
                if context.current_buffer or context.is_in_protected_element():
                    # 如果有保护元素，先切分保护元素
                    if context.is_in_protected_element():
                        # 退出保护元素并切块
                        protected_blocks = self._flush_protected_element(context, file_path)
                        for block in protected_blocks:
                            blocks.append(block)
                    # 再切分普通缓冲区
                    block = self._flush_buffer(context, file_path)
                    if block:
                        blocks.append(block)

                # 重置is_splited状态，因为新标题开始了新的逻辑单元
                context.is_splited_since_last_header = False

                # 更新上下文状态
                lvl = row.header_level  # 1~6
                context.reset_on_new_header(lvl)
                context.set_heading_text(lvl, row.clean_text)

                # 标题行本身作为新缓冲区的开始
                context.clear_buffer()
                context.append_to_buffer(row)
                i += 1
                continue

            # 2. 如果是标签行
            if row.is_tag:
                # 确定标签级别：当前标题级别
                current_lvl = 0
                for idx in range(1, 7):
                    if context.heading_stack[idx] is not None:
                        current_lvl = idx
                tag = self.tag_node.extract_from_text(row.clean_text)
                if tag:
                    context.add_tag(tag, current_lvl)
                i += 1
                continue

            # 3. 检测代码块边界
            if row.is_code_fence:
                # 在进入代码块之前，先切分当前缓冲区（如果有内容）
                if not context.in_code_block and context.current_buffer:
                    # 非标题行切块，设置状态
                    context.is_splited_since_last_header = True
                    block = self._flush_buffer(context, file_path)
                    if block:
                        blocks.append(block)
                
                if not context.in_code_block:
                    # 进入代码块保护元素
                    element_id = f"code_{row.index}"
                    context.enter_protected_element(element_id, 'code', row.index)
                    context.add_row_to_protected_element(row)
                else:
                    # 退出代码块保护元素
                    context.add_row_to_protected_element(row)
                    context.is_splited_since_last_header = True
                    protected_blocks = self._flush_protected_element(context, file_path)
                    for block in protected_blocks:
                        blocks.append(block)
                    context.exit_protected_element()
                i += 1
                continue

            # 4. 检测表格行
            if row.is_table:
                # 在进入表格之前，先切分当前缓冲区（如果有内容）
                if not context.in_table_block and context.current_buffer:
                    # 非标题行切块，设置状态
                    context.is_splited_since_last_header = True
                    block = self._flush_buffer(context, file_path)
                    if block:
                        blocks.append(block)
                
                # 如果当前不在表格保护元素中，则进入新的表格保护元素
                if not context.in_table_block:
                    element_id = f"table_{row.index}"
                    context.enter_protected_element(element_id, 'table', row.index)
                context.add_row_to_protected_element(row)
                i += 1
                # 检查下一行是否仍然是表格行，如果不是则退出表格保护元素
                if i < len(rows) and not rows[i].is_table:
                    context.is_splited_since_last_header = True
                    protected_blocks = self._flush_protected_element(context, file_path)
                    for block in protected_blocks:
                        blocks.append(block)
                    context.exit_protected_element()
                continue

            # 5. 如果当前处于保护元素内部（代码块或表格内部行）
            if context.is_in_protected_element():
                context.add_row_to_protected_element(row)
                i += 1
                continue

            # 6. 普通内容行
            context.append_to_buffer(row)

            # 7. 检查缓冲区是否超长
            current_len = context.buffer_length()
            if current_len > self.config.chunk_max_chars:
                # 超长切块，属于非标题行切块，设置状态
                context.is_splited_since_last_header = True
                block = self._flush_buffer(context, file_path)
                if block:
                    blocks.append(block)
                # 保留重叠行
                overlap = self.config.chunk_overlap
                if overlap > 0:
                    # 从当前缓冲区中保留最后overlap行
                    buffer_rows = context.flush_buffer()
                    keep_rows = buffer_rows[-overlap:] if len(buffer_rows) >= overlap else buffer_rows
                    for r in keep_rows:
                        context.append_to_buffer(r)
                else:
                    context.clear_buffer()
            else:
                i += 1

        # 收尾处理：处理剩余的保护元素和缓冲区
        if context.is_in_protected_element():
            block = self._flush_protected_element(context, file_path)
            if block:
                blocks.append(block)
            context.exit_protected_element()

        if context.current_buffer:
            block = self._flush_buffer(context, file_path)
            if block:
                blocks.append(block)

        return blocks

    def _flush_buffer(self, context: ParsingContext, file_path: str) -> Optional[ParsedBlock]:
        """将当前缓冲区中的行切分为一个块"""
        rows = context.flush_buffer()
        if not rows:
            return None

        # 去除首尾的空行（整行为空或只包含空白字符）
        while rows and rows[0].text.strip() == "":
            rows.pop(0)
        while rows and rows[-1].text.strip() == "":
            rows.pop(-1)

        if not rows:
            return None

        text = "".join(r.text for r in rows).strip()
        if not text:
            return None

        # 舍弃仅包含标题的块
        if self._should_discard_block(text):
            return None

        active_tags = context.get_active_tags()
        header_path = context.get_header_path()

        # 添加 file_path 作为 tag
        file_tag = Tag(key="file_path", value=file_path, original_text=f"#file_path/{file_path}")
        active_tags.append(file_tag)
        
        # 如果 header_path 非空，添加 title tag
        if header_path:
            title_tag = Tag(key="title", value=header_path, original_text=f"#title/{header_path}")
            active_tags.append(title_tag)

        # 生成跨文件唯一的block_id
        base_content_hash = hashlib.md5(text.encode()).hexdigest()[:16]
        bid = hashlib.md5(f"{file_path}_{rows[0].index}_{rows[-1].index}_{base_content_hash}".encode()).hexdigest()

        # 行号转换为1-based（文件行号）
        start_line = rows[0].index + 1
        end_line = rows[-1].index + 1

        return ParsedBlock(
            block_id=bid,
            content=text,
            start_line=start_line,
            end_line=end_line,
            tags=list(active_tags),
            is_splited=context.is_splited_since_last_header,
            protected_element_type=None,  # 普通块没有保护元素类型
            protected_element_overlength=False  # 普通块没有保护元素超长
        )

    def _flush_protected_element(self, context: ParsingContext, file_path: str) -> List[ParsedBlock]:
        """将当前保护元素切分为一个或多个块（如果超长则使用特殊切块器拆分）"""
        if not context.current_protected_element_id:
            return []

        rows = context.get_protected_element_rows(context.current_protected_element_id)
        if not rows:
            return []

        text = "".join(r.text for r in rows).strip()
        if not text:
            return []

        active_tags = context.get_active_tags()
        header_path = context.get_header_path()

        # 添加 file_path 作为 tag
        file_tag = Tag(key="file_path", value=file_path, original_text=f"#file_path/{file_path}")
        active_tags.append(file_tag)
        
        # 如果 header_path 非空，添加 title tag
        if header_path:
            title_tag = Tag(key="title", value=header_path, original_text=f"#title/{header_path}")
            active_tags.append(title_tag)

        # 检查保护元素是否单独超长
        element_len = sum(len(r.text) for r in rows)
        is_splited = context.is_splited_since_last_header
        protected_element_overlength = element_len > self.config.chunk_max_chars

        # 行号转换为1-based（文件行号）
        start_line = rows[0].index + 1
        end_line = rows[-1].index + 1

        # 生成基础ID（跨文件唯一）
        base_content_hash = hashlib.md5(text.encode()).hexdigest()[:16]
        base_id = hashlib.md5(f"{file_path}_{start_line}_{end_line}_{base_content_hash}".encode()).hexdigest()

        if not protected_element_overlength:
            # 未超长，返回单个块
            return [ParsedBlock(
                block_id=base_id,
                content=text,
                start_line=start_line,
                end_line=end_line,
                tags=list(active_tags),
                is_splited=is_splited,
                protected_element_type=context.current_protected_type,
                protected_element_overlength=False
            )]
        else:
            # 超长保护元素，使用特殊切块器拆分
            chunks = self.special_chunker.chunk_protected_element(
                element_type=context.current_protected_type,
                content=text,
                original_tags=active_tags,
                max_chars=self.config.chunk_max_chars
            )
            
            blocks = []
            total_chunks = len(chunks)
            for idx, (chunk_text, chunk_tags) in enumerate(chunks):
                # 为每个子块生成带序号的ID
                chunk_id = f"{base_id}_{str(idx+1).zfill(3)}"  # 001, 002, ...
                
                # 估算子块的行号范围（简化：按比例分配）
                if total_chunks == 1:
                    chunk_start = start_line
                    chunk_end = end_line
                else:
                    # 简单按字符比例估算行号
                    total_chars = len(text)
                    chunk_chars = len(chunk_text)
                    chunk_ratio = chunk_chars / total_chars
                    total_lines = end_line - start_line + 1
                    chunk_lines = max(1, int(total_lines * chunk_ratio))
                    chunk_start = start_line + int((total_lines - chunk_lines) * idx / total_chunks)
                    chunk_end = chunk_start + chunk_lines - 1
                    # 确保最后一个子块结束行不超过原始结束行
                    if idx == total_chunks - 1:
                        chunk_end = end_line
                
                blocks.append(ParsedBlock(
                    block_id=chunk_id,
                    content=chunk_text,
                    start_line=chunk_start,
                    end_line=chunk_end,
                    tags=chunk_tags,
                    is_splited=True,  # 超长切分的块标记为已切分
                    protected_element_type=context.current_protected_type,
                    protected_element_overlength=False  # 子块本身不超长
                ))
            
            return blocks
