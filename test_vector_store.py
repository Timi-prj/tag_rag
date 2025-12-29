#!/usr/bin/env python3
"""
向量存储模块测试脚本
测试TextAugmenterNode、ChromaDBStoreNode和VectorStorePipeline（模拟嵌入）
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.common.types import ParsedBlock, Tag
from src.config.manager import ConfigManager
from src.modules.vector_store.nodes.text_augmenter import TextAugmenterNode
from src.modules.vector_store.nodes.chroma_store import ChromaDBStoreNode
from src.modules.vector_store.nodes.pipeline import VectorStorePipeline

def test_text_augmenter():
    """测试文本增强节点"""
    print("测试 TextAugmenterNode...")
    augmenter = TextAugmenterNode()
    
    # 创建测试块
    block1 = ParsedBlock(
        block_id="test1",
        content="这是一段普通文本",
        start_line=1,
        end_line=2,
        tags=[Tag(key="主题", value="测试", original_text="?主题:测试")]
    )
    
    block2 = ParsedBlock(
        block_id="test2",
        content="print('hello world')",
        start_line=3,
        end_line=4,
        tags=[],
        protected_element_type="code"
    )
    
    # 测试单块增强
    augmented1 = augmenter.augment_batch([block1])[0]
    assert "主题: 测试" in augmented1
    assert "这是一段普通文本" in augmented1
    print(f"  块1增强文本: {augmented1}")
    
    # 测试保护元素不增强
    augmented2 = augmenter.augment_batch([block2])[0]
    assert augmented2 == block2.content
    print(f"  块2（代码块）未增强: {augmented2}")
    
    # 测试批量处理
    blocks = [block1, block2]
    results = augmenter.process(blocks)
    assert len(results) == 2
    print("  TextAugmenterNode测试通过！")
    return True

def test_chroma_store():
    """测试ChromaDB存储节点"""
    print("测试 ChromaDBStoreNode...")
    config = ConfigManager()
    store = ChromaDBStoreNode(config)
    
    # 创建测试块
    block = ParsedBlock(
        block_id="chroma_test1",
        content="测试内容",
        start_line=1,
        end_line=1,
        tags=[Tag(key="测试", value="值", original_text="?测试:值")]
    )
    
    # 模拟向量
    mock_vector = [0.1] * config.vector_dim
    
    # 存储单个向量
    store.store_single(mock_vector, block)
    print(f"  存储块: {block.block_id}")
    
    # 获取集合统计
    count = store.get_collection_stats()
    print(f"  集合统计（文档数）: {count}")
    
    # 清理测试数据
    store.collection.delete(ids=[block.block_id])
    print("  ChromaDBStoreNode测试通过！")
    return True

def test_pipeline_with_mock_embedding():
    """测试管道，使用模拟嵌入"""
    print("测试 VectorStorePipeline（模拟嵌入）...")
    
    # 创建模拟嵌入节点
    class MockEmbeddingNode:
        def __init__(self, config):
            self.config = config
            self.dimension = config.vector_dim
            
        def process(self, texts):
            # 返回模拟向量
            return [[0.5] * self.dimension for _ in texts]
        
        def get_dimension(self):
            return self.dimension
    
    config = ConfigManager()
    
    # 创建管道，注入模拟嵌入节点
    augmenter = TextAugmenterNode(config)
    embedder = MockEmbeddingNode(config)
    store = ChromaDBStoreNode(config)
    
    pipeline = VectorStorePipeline(
        config=config,
        augmenter=augmenter,
        embedder=embedder,
        store=store
    )
    
    # 创建测试块
    blocks = [
        ParsedBlock(
            block_id=f"pipeline_test_{i}",
            content=f"测试内容{i}",
            start_line=i*10,
            end_line=i*10+5,
            tags=[Tag(key="标签", value=f"值{i}", original_text=f"?标签:值{i}")]
        )
        for i in range(3)
    ]
    
    # 处理块
    success, failure, failed_ids = pipeline.process_blocks(blocks, show_progress=False)
    
    print(f"  处理结果: {success} 成功, {failure} 失败")
    print(f"  失败块ID: {failed_ids}")
    
    # 清理测试数据
    store.collection.delete(ids=[b.block_id for b in blocks])
    
    assert success == 3
    assert failure == 0
    print("  VectorStorePipeline测试通过！")
    return True

def main():
    """主测试函数"""
    print("开始向量存储模块测试...")
    
    try:
        test_text_augmenter()
        test_chroma_store()
        test_pipeline_with_mock_embedding()
        
        print("\n✅ 所有测试通过！")
        return 0
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
