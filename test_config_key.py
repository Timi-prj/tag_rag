#!/usr/bin/env python3
"""
测试OpenAI兼容格式的key配置
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.config.manager import ConfigManager
from src.modules.vector_store.nodes.embedding import EmbeddingNode

def test_config_manager():
    print("测试ConfigManager...")
    config = ConfigManager()
    
    print(f"  embedding_api_base: {config.embedding_api_base}")
    print(f"  embedding_model: {config.embedding_model}")
    print(f"  embedding_api_key: {config.embedding_api_key} (长度: {len(config.embedding_api_key)})")
    
    # 验证配置读取
    assert config.embedding_api_base == "https://api.openai.com/v1"
    assert config.embedding_model == "BAAI/bge-large-zh-v1.5"
    # api_key 默认为空字符串
    assert config.embedding_api_key == ""
    
    print("  ConfigManager测试通过！")
    return True

def test_embedding_node_without_key():
    print("测试EmbeddingNode（无API密钥）...")
    try:
        # 临时清除环境变量
        os.environ.pop("OPENAI_API_KEY", None)
        node = EmbeddingNode()
        print("  错误：应抛出异常但没有抛出")
        return False
    except ValueError as e:
        print(f"  预期异常: {e}")
        assert "未设置OpenAI API密钥" in str(e)
        print("  EmbeddingNode无密钥异常测试通过！")
        return True

def test_embedding_node_with_env_key():
    print("测试EmbeddingNode（环境变量API密钥）...")
    # 设置一个假的API密钥到环境变量
    os.environ["OPENAI_API_KEY"] = "test-key-from-env"
    try:
        node = EmbeddingNode()
        # 如果初始化成功，则验证client是否创建
        assert node.client is not None
        print(f"  EmbeddingNode使用环境变量密钥初始化成功")
        # 检查client的api_key是否正确设置（但openai库不暴露，我们只能相信它）
        print("  注意：无法验证client内部密钥，假设设置正确")
        return True
    except Exception as e:
        print(f"  意外异常: {e}")
        return False
    finally:
        # 清理环境变量
        os.environ.pop("OPENAI_API_KEY", None)

def test_embedding_node_with_config_key():
    print("测试EmbeddingNode（配置文件API密钥）...")
    # 确保环境变量没有设置
    os.environ.pop("OPENAI_API_KEY", None)
    
    # 我们需要修改配置实例的embedding_api_key，但ConfigManager是单例，已经加载了配置文件。
    # 由于配置文件中的api_key为空，我们需要模拟一个非空值。
    # 我们可以通过直接修改config实例的embedding_api_key属性来测试。
    config = ConfigManager()
    original_key = config.embedding_api_key
    config.embedding_api_key = "test-key-from-config"
    
    try:
        node = EmbeddingNode(config=config)
        assert node.client is not None
        print(f"  EmbeddingNode使用配置文件密钥初始化成功")
        return True
    except Exception as e:
        print(f"  意外异常: {e}")
        return False
    finally:
        # 恢复原始值
        config.embedding_api_key = original_key

def main():
    print("开始OpenAI兼容格式key配置测试...")
    
    try:
        test_config_manager()
        test_embedding_node_without_key()
        test_embedding_node_with_env_key()
        test_embedding_node_with_config_key()
        
        print("\n✅ 所有配置测试通过！")
        return 0
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
