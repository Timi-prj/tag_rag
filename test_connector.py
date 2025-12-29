#!/usr/bin/env python3
"""
测试VectorStoreConnector
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.config.manager import ConfigManager
from src.common.types import ParsedBlock, Tag
from src.modules.vector_store.connector import VectorStoreConnector

def main():
    print('测试 VectorStoreConnector 初始化...')
    connector = VectorStoreConnector()
    print('VectorStoreConnector 初始化成功')

    # 创建测试块
    blocks = [
        ParsedBlock(
            block_id='connector_test_1',
            content='这是一个测试文档内容',
            start_line=1,
            end_line=3,
            tags=[Tag(key='类别', value='测试', original_text='?类别:测试')]
        ),
        ParsedBlock(
            block_id='connector_test_2',
            content='print("代码块")',
            start_line=4,
            end_line=5,
            tags=[],
            protected_element_type='code'
        )
    ]

    print(f'准备保存 {len(blocks)} 个块...')
    connector.save_blocks(blocks)
    print('save_blocks 调用完成（注意：如果没有 OPENAI_API_KEY，可能会使用占位模式）')
    return 0

if __name__ == "__main__":
    sys.exit(main())
