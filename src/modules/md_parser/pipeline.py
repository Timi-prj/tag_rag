import os
import concurrent.futures
from typing import List, Optional
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
    支持多线程批量处理和可变参数文件处理
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
            # Stage 1: IO 读取，尝试多种编码以兼容不同格式
            raw_lines = None
            encodings_to_try = ['utf-8-sig', 'utf-8', 'utf-16', 'gbk', 'latin-1']
            
            for encoding in encodings_to_try:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        raw_lines = f.readlines()
                    # 如果成功读取，则退出循环
                    break
                except UnicodeDecodeError:
                    continue
            
            if raw_lines is None:
                print(f"[Error] Failed to decode {file_path} with tried encodings: {encodings_to_try}")
                return []

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

    def process_files(self, *file_paths: str) -> List[ParsedBlock]:
        """
        处理可变数量的文件，支持多线程批量处理
        
        Args:
            *file_paths: 可变数量的文件路径
            
        Returns:
            List[ParsedBlock]: 所有文件的块合并列表
        """
        if not file_paths:
            return []
        
        all_blocks = []
        
        # 使用线程池处理多个文件
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(file_paths), 4)) as executor:
            # 提交任务
            future_to_file = {executor.submit(self.run, fp): fp for fp in file_paths}
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    blocks = future.result()
                    all_blocks.extend(blocks)
                    print(f"[Info] Processed {file_path}: {len(blocks)} blocks")
                except Exception as e:
                    print(f"[Error] Failed to process {file_path}: {e}")
        
        return all_blocks

    def process_directory(self, input_dir: Optional[str] = None) -> List[ParsedBlock]:
        """
        处理指定目录下的所有文件（根据配置的后缀白名单）
        
        Args:
            input_dir: 输入目录路径，如果为None则使用配置中的input_dir
            
        Returns:
            List[ParsedBlock]: 所有文件的块合并列表
        """
        if input_dir is None:
            input_dir = self.config.input_dir
        
        if not os.path.exists(input_dir):
            print(f"[Warning] Directory not found: {input_dir}")
            return []
        
        # 收集所有符合后缀的文件
        file_paths = []
        for root, dirs, files in os.walk(input_dir):
            for file in files:
                if any(file.endswith(ext) for ext in self.config.file_extensions):
                    file_paths.append(os.path.join(root, file))
        
        if not file_paths:
            print(f"[Info] No files found with extensions {self.config.file_extensions} in {input_dir}")
            return []
        
        print(f"[Info] Found {len(file_paths)} files to process")
        return self.process_files(*file_paths)
