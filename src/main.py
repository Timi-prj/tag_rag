import os
import sys
import json
import argparse
from dataclasses import asdict
from typing import List

# 路径 Hack (确保 Docker 容器内能找到包)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.common.logger import configure_logging, get_logger

from src.config.manager import ConfigManager
from src.modules.md_parser.pipeline import MarkdownParserPipeline
from src.modules.vector_store.connector import VectorStoreConnector


def process_files(*file_paths: str, output_json: bool = True) -> List[dict]:
    """
    抽象方法：处理可变数量的文件，返回解析后的块字典列表
    
    Args:
        *file_paths: 可变数量的文件路径
        output_json: 是否将结果保存为JSON文件
        
    Returns:
        List[dict]: 所有文件的块字典列表
    """
    # 初始化日志
    config = ConfigManager()
    configure_logging({
        'level': config.log_level,
        'format': config.log_format,
        'handlers': config.log_handlers
    })
    logger = get_logger('tag_rag.main')
    
    logger.info("System Initializing...")
    
    # 实例化模块一 (解析管道)
    parser_pipeline = MarkdownParserPipeline()
    
    # 实例化模块二 (向量存储连接器)
    vector_store = VectorStoreConnector()

    if not file_paths:
        # 如果没有提供文件路径，则处理配置目录下的所有文件
        logger.info(f"No files specified, processing directory: {config.input_dir}")
        blocks = parser_pipeline.process_directory()
    else:
        # 处理指定的文件列表
        logger.info(f"Processing {len(file_paths)} specified file(s)...")
        blocks = parser_pipeline.process_files(*file_paths)
    
    logger.info(f"Generated {len(blocks)} blocks in total.")
    
    # 保存中间结果 (可选，方便调试)
    if output_json:
        os.makedirs(config.output_dir, exist_ok=True)
        out_path = os.path.join(config.output_dir, "parsed_result.json")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump([asdict(b) for b in blocks], f, ensure_ascii=False, indent=2)
        logger.info(f"Intermediate result saved to {out_path}")
    
    # 模块二消费
    logger.info("Running Module 2: Vectorizing...")
    vector_store.save_blocks(blocks)
    
    logger.info("Done.")
    return [asdict(b) for b in blocks]


def process_directory(directory_path: str = None, output_json: bool = True) -> List[dict]:
    """
    处理指定目录下的所有文件（根据配置的后缀白名单）
    
    Args:
        directory_path: 目录路径，如果为None则使用配置中的input_dir
        output_json: 是否将结果保存为JSON文件
        
    Returns:
        List[dict]: 所有文件的块字典列表
    """
    # 初始化日志
    config = ConfigManager()
    configure_logging({
        'level': config.log_level,
        'format': config.log_format,
        'handlers': config.log_handlers
    })
    logger = get_logger('tag_rag.main')
    
    logger.info("System Initializing...")
    
    # 实例化模块一 (解析管道)
    parser_pipeline = MarkdownParserPipeline()
    
    # 实例化模块二 (向量存储连接器)
    vector_store = VectorStoreConnector()

    logger.info(f"Processing directory: {directory_path or config.input_dir}")
    blocks = parser_pipeline.process_directory(directory_path)
    
    logger.info(f"Generated {len(blocks)} blocks in total.")
    
    # 保存中间结果 (可选，方便调试)
    if output_json:
        os.makedirs(config.output_dir, exist_ok=True)
        out_path = os.path.join(config.output_dir, "parsed_result.json")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump([asdict(b) for b in blocks], f, ensure_ascii=False, indent=2)
        logger.info(f"Intermediate result saved to {out_path}")
    
    # 模块二消费
    logger.info("Running Module 2: Vectorizing...")
    vector_store.save_blocks(blocks)
    
    logger.info("Done.")
    return [asdict(b) for b in blocks]


def main():
    """命令行入口点"""
    parser = argparse.ArgumentParser(description='Tag RAG Markdown Parser')
    parser.add_argument('files', nargs='*', help='Markdown files to process (if none, process all files in config.input_dir)')
    parser.add_argument('--dir', help='Directory to process (overrides config.input_dir)')
    parser.add_argument('--no-json', action='store_true', help='Do not save JSON output')
    parser.add_argument('--no-vectorize', action='store_true', help='Do not vectorize blocks')
    
    args = parser.parse_args()
    
    # 初始化日志
    config = ConfigManager()
    configure_logging({
        'level': config.log_level,
        'format': config.log_format,
        'handlers': config.log_handlers
    })
    logger = get_logger('tag_rag.main')
    
    logger.info("System Initializing...")
    
    # 实例化模块一 (解析管道)
    parser_pipeline = MarkdownParserPipeline()
    
    # 实例化模块二 (向量存储连接器)
    vector_store = VectorStoreConnector()

    blocks = []
    
    # 确定要处理的文件
    if args.dir:
        # 处理指定目录
        logger.info(f"Processing directory: {args.dir}")
        blocks = parser_pipeline.process_directory(args.dir)
    elif args.files:
        # 处理指定的文件列表
        logger.info(f"Processing {len(args.files)} specified file(s)...")
        blocks = parser_pipeline.process_files(*args.files)
    else:
        # 默认处理配置目录下的所有文件
        logger.info(f"No files specified, processing directory: {config.input_dir}")
        blocks = parser_pipeline.process_directory()
    
    logger.info(f"Generated {len(blocks)} blocks in total.")
    
    # 保存中间结果 (可选，方便调试)
    if not args.no_json:
        os.makedirs(config.output_dir, exist_ok=True)
        out_path = os.path.join(config.output_dir, "parsed_result.json")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump([asdict(b) for b in blocks], f, ensure_ascii=False, indent=2)
        logger.info(f"Intermediate result saved to {out_path}")
    
    # 模块二消费
    if not args.no_vectorize:
        logger.info("Running Module 2: Vectorizing...")
        vector_store.save_blocks(blocks)
    
    logger.info("Done.")


if __name__ == "__main__":
    main()
