import os
import sys
import json
from dataclasses import asdict

# 路径 Hack (确保 Docker 容器内能找到包)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config.manager import ConfigManager
from src.modules.md_parser.pipeline import MarkdownParserPipeline
from src.modules.vector_store.connector import VectorStoreConnector

def main():
    # --- 初始化 ---
    print(">>> System Initializing...")
    config = ConfigManager()
    
    # 实例化模块一 (解析管道)
    parser_pipeline = MarkdownParserPipeline()
    
    # 实例化模块二 (向量存储连接器)
    vector_store = VectorStoreConnector()

    # --- 准备测试数据 ---
    input_file = "test.md"
    # 如果文件不存在，创建一个假的用于演示
    if not os.path.exists(input_file):
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write("# Project Alpha\n\n#?status/active\n\nIntroduction to the project.\n\n## Section 1\nDetails here.")

    # --- 执行流程 ---
    print(f">>> Running Module 1: Parsing {input_file}...")
    
    # 1. 调用管道处理文件
    blocks = parser_pipeline.run(input_file)
    print(f"    Generated {len(blocks)} blocks.")

    # 2. 保存中间结果 (可选，方便调试)
    os.makedirs(config.output_dir, exist_ok=True)
    out_path = os.path.join(config.output_dir, "parsed_result.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump([asdict(b) for b in blocks], f, ensure_ascii=False, indent=2)
    print(f"    Intermediate result saved to {out_path}")

    # --- 模块二消费 ---
    print(">>> Running Module 2: Vectorizing...")
    vector_store.save_blocks(blocks)
    
    print(">>> Done.")

if __name__ == "__main__":
    main()
