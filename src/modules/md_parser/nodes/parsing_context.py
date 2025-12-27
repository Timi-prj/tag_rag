from typing import List, Dict, Optional
from src.common.types import Tag
from src.modules.md_parser.nodes.row_parser import Row


class ParsingContext:
    """
    解析上下文状态机，负责管理解析过程中的所有状态。
    标题栈与作用域标签结构对齐：
      - 级别0：文档级别（无标题文本）
      - 级别1~6：对应H1~H6标题
    作用域标签同样使用0~6，0代表文档，1~6代表H1~H6。
    """

    def __init__(self):
        # 标题栈，索引0为文档级别（None），索引1~6对应H1~H6
        # 例如：heading_stack[1] 存储H1标题文本，heading_stack[2] 存储H2标题文本
        self.heading_stack: List[Optional[str]] = [None] * 7  # 0~6

        # 作用域标签，key为级别（0=文档，1=H1，...，6=H6）
        self.scope_tags: Dict[int, List[Tag]] = {i: [] for i in range(7)}  # 0~6

        # 当前缓冲区，存放尚未形成块的普通行
        self.current_buffer: List[Row] = []

        # 保护元素分组，key为元素ID，value为该元素包含的所有行
        self.protected_element_groups: Dict[str, List[Row]] = {}

        # 当前保护元素ID（如果当前行属于某个保护元素）
        self.current_protected_element_id: Optional[str] = None

        # 当前保护元素类型：'code' 或 'table'
        self.current_protected_type: Optional[str] = None

        # 是否处于代码块内部（用于跟踪 ``` 边界）
        self.in_code_block: bool = False

        # 是否处于表格连续行中（用于表格分组）
        self.in_table_block: bool = False

        # 状态：自上标题行后是否发生过非标题行切块
        self.is_splited_since_last_header: bool = False

    def reset_on_new_header(self, header_level: int):
        """
        当遇到新标题时，清除当前级别及更深级别的标签。
        header_level: 1~6 对应 H1~H6
        """
        # 清除当前级别及更深级别的旧标签（级别1~6）
        for i in range(header_level, 7):
            self.scope_tags[i] = []

        # 注意：标题栈不需要调整大小，因为已经固定长度为7
        # 但需要清除当前级别及更深级别的标题文本
        for i in range(header_level, 7):
            self.heading_stack[i] = None

    def set_heading_text(self, header_level: int, text: str):
        """设置当前级别标题文本，header_level为1~6"""
        self.heading_stack[header_level] = text

    def add_tag(self, tag: Tag, level: int):
        """添加标签到指定级别，level为0~6"""
        if level in self.scope_tags:
            self.scope_tags[level].append(tag)

    def enter_protected_element(self, element_id: str, element_type: str, start_index: int):
        """进入保护元素区域"""
        self.current_protected_element_id = element_id
        self.current_protected_type = element_type
        self.protected_element_groups[element_id] = []

        if element_type == 'code':
            self.in_code_block = True
        elif element_type == 'table':
            self.in_table_block = True

    def exit_protected_element(self):
        """退出保护元素区域"""
        # 清除当前保护元素分组
        if self.current_protected_element_id:
            self.clear_protected_element(self.current_protected_element_id)
        self.current_protected_element_id = None
        self.current_protected_type = None
        self.in_code_block = False
        self.in_table_block = False

    def add_row_to_protected_element(self, row: Row):
        """将行添加到当前保护元素分组"""
        if self.current_protected_element_id:
            self.protected_element_groups[self.current_protected_element_id].append(row)

    def is_in_protected_element(self) -> bool:
        """是否处于保护元素内部"""
        return self.current_protected_element_id is not None

    def get_active_tags(self) -> List[Tag]:
        """收集所有当前有效的标签（继承逻辑）"""
        active_tags = []
        # 确定当前标题级别：找到最大的非None标题索引
        current_lvl = 0
        for i in range(1, 7):
            if self.heading_stack[i] is not None:
                current_lvl = i
        # 遍历所有父级，收集标签（包括文档级别0）
        for i in range(0, current_lvl + 1):
            if i in self.scope_tags:
                active_tags.extend(self.scope_tags[i])
        return active_tags

    def get_header_path(self) -> str:
        """生成标题路径字符串，过滤掉None，忽略索引0（文档级别）"""
        valid_headers = [h for h in self.heading_stack[1:] if h is not None]
        return "/".join(valid_headers)

    def flush_buffer(self) -> List[Row]:
        """清空当前缓冲区并返回内容，用于生成块"""
        buffer = self.current_buffer.copy()
        self.current_buffer.clear()
        return buffer

    def clear_buffer(self):
        """清空缓冲区但不返回内容"""
        self.current_buffer.clear()

    def append_to_buffer(self, row: Row):
        """将行添加到缓冲区"""
        self.current_buffer.append(row)

    def buffer_length(self) -> int:
        """计算缓冲区中文本的总字符数"""
        return sum(len(r.text) for r in self.current_buffer)

    def get_protected_element_rows(self, element_id: str) -> List[Row]:
        """获取指定保护元素ID的所有行"""
        return self.protected_element_groups.get(element_id, [])

    def clear_protected_element(self, element_id: str):
        """清除指定的保护元素分组（通常在切块后清除）"""
        if element_id in self.protected_element_groups:
            del self.protected_element_groups[element_id]
