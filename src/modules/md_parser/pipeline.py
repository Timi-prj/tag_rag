import os
from typing import List
from src.config.manager import ConfigManager
from src.common.types import ParsedBlock
# 导入各个独立的节点
from src.modules.md_parser.nodes.row_parser import RowParserNode
from src.modules.md_parser.nodes.tag_extractor import TagExtractorNode
from src.modules.md_parser.nodes.scope_builder import ScopeBuilderNode

class MarkdownParserPipeline:
    """
    模块一的总控管道
    职责: 编排各个节点，将 Markdown 文件转换为结构化 Blocks
    """

    def __init__(self):
        # 1. 获取单例配置
        self.config = ConfigManager()

        # 2. 初始化各节点 (组装流水线)
        # 节点1: 负责基础行识别
        self.row_parser = RowParserNode()
        
        # 节点2: 负责标签清洗
        self.tag_extractor = TagExtractorNode(self.config)
        
        # 节点3: 负责上下文作用域合并 (它依赖节点2)
        self.scope_builder = ScopeBuilderNode(self.config, self.tag_extractor)

    def run(self, file_path: str) -> List[ParsedBlock]:
        """
        执行流水线: File -> Rows -> Blocks
        """
        if not os.path.exists(file_path):
            print(f"[Warning] File not found: {file_path}")
            return []

        try:
            # Stage 1: IO 读取
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_lines = f.readlines()

            # Stage 2: 行级解析 (Raw Strings -> Row Objects)
            rows = self.row_parser.process(raw_lines)

            # Stage 3: 结构化构建 (Row Objects -> ParsedBlocks)
            # 这一步内部会自动处理标签提取和标题作用域
            blocks = self.scope_builder.run(rows, file_path)

            return blocks

        except Exception as e:
            print(f"[Error] Failed to process {file_path}: {e}")
            # 根据需求，这里可以选择 raise 抛出异常或者返回空列表
            return []
