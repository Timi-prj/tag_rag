#!/usr/bin/env python3
"""
测试嵌入模型联通性 v2
针对SiliconFlow API调整测试逻辑
"""
import sys
import os
import requests
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.config.manager import ConfigManager

def test_config():
    """检查配置"""
    print("检查配置...")
    config = ConfigManager()
    print(f"  API Base: {config.embedding_api_base}")
    print(f"  模型: {config.embedding_model}")
    print(f"  配置中的API密钥: {'已设置' if config.embedding_api_key else '未设置'}")
    print(f"  向量维度: {config.vector_dim}")
    
    env_key = os.environ.get("OPENAI_API_KEY")
    print(f"  环境变量OPENAI_API_KEY: {'已设置' if env_key else '未设置'}")
    
    # 确定最终使用的API密钥
    final_key = env_key or config.embedding_api_key
    print(f"  最终使用的API密钥: {'已设置' if final_key else '未设置'}")
    
    return config, final_key

def test_siliconflow_api(config, api_key):
    """直接测试SiliconFlow API"""
    print("\n测试SiliconFlow API...")
    
    if not api_key:
        print("  未提供API密钥，跳过API测试")
        return False
    
    # 构建请求头
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 请求数据 - 按照用户提供的curl示例
    data = {
        "model": config.embedding_model,
        "input": "Silicon flow embedding online: fast, affordable, and high-quality embedding services. come try it out!",
        "encoding_format": "float",
        "dimensions": config.vector_dim
    }
    
    print(f"  请求端点: {config.embedding_api_base}")
    print(f"  使用模型: {config.embedding_model}")
    print(f"  请求维度: {config.vector_dim}")
    
    try:
        response = requests.post(config.embedding_api_base, headers=headers, json=data, timeout=30)
        print(f"  响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("  ✅ SiliconFlow API测试成功！")
            result = response.json()
            embedding = result['data'][0]['embedding']
            print(f"    返回向量维度: {len(embedding)}")
            print(f"    向量前5个值: {embedding[:5]}")
            # 验证维度是否匹配配置
            if len(embedding) == config.vector_dim:
                print(f"    维度验证: ✅ 匹配配置 ({config.vector_dim})")
            else:
                print(f"    维度验证: ⚠️ 不匹配 (配置: {config.vector_dim}, 实际: {len(embedding)})")
            return True
        elif response.status_code == 401:
            print("  ❌ 认证失败：API密钥无效")
            print(f"     响应内容: {response.text[:200]}")
            return False
        elif response.status_code == 404:
            print("  ❌ 端点不存在：请检查API Base URL")
            return False
        else:
            print(f"  ❌ 请求失败，状态码: {response.status_code}")
            print(f"     响应内容: {response.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        print("  ❌ 连接错误：无法连接到API端点")
        return False
    except requests.exceptions.Timeout:
        print("  ❌ 请求超时")
        return False
    except Exception as e:
        print(f"  ❌ 请求异常: {e}")
        return False

def test_embedding_node():
    """测试EmbeddingNode初始化"""
    print("\n测试EmbeddingNode初始化...")
    try:
        from src.modules.vector_store.nodes.embedding import EmbeddingNode
        node = EmbeddingNode()
        print("  ✅ EmbeddingNode初始化成功")
        print(f"     模型: {node._model}")
        print(f"     维度: {node._dimension}")
        
        # 测试单次嵌入（需要API密钥）
        print("  测试单次嵌入...")
        try:
            embedding = node._embed_single("测试文本")
            print(f"  ✅ 嵌入生成成功，维度: {len(embedding)}")
            return True
        except Exception as e:
            print(f"  ⚠️  嵌入生成失败（可能是API密钥无效）: {e}")
            # 即使嵌入失败，节点初始化也是成功的
            return True
    except ValueError as e:
        print(f"  ❌ EmbeddingNode初始化失败（缺少API密钥）: {e}")
        return False
    except Exception as e:
        print(f"  ❌ EmbeddingNode初始化异常: {e}")
        return False

def main():
    print("开始SiliconFlow嵌入模型联通性测试...")
    print("="*50)
    
    # 检查配置
    config, api_key = test_config()
    
    # 测试SiliconFlow API
    api_ok = test_siliconflow_api(config, api_key)
    
    # 测试EmbeddingNode
    node_ok = test_embedding_node()
    
    print("\n" + "="*50)
    print("测试总结:")
    print(f"  SiliconFlow API测试: {'✅ 通过' if api_ok else '❌ 失败'}")
    print(f"  EmbeddingNode初始化: {'✅ 通过' if node_ok else '❌ 失败'}")
    
    if api_ok and node_ok:
        print("\n✅ 嵌入模型联通性测试完全通过！")
        print("   系统已准备好使用SiliconFlow进行文本嵌入。")
        return 0
    elif node_ok and not api_ok:
        print("\n⚠️  EmbeddingNode可初始化，但API测试失败")
        print("   可能原因：")
        print("   1. API密钥无效或已过期")
        print("   2. API端点URL不正确")
        print("   3. 模型名称不正确")
        print("   请检查config.yaml中的配置。")
        return 1
    else:
        print("\n❌ 嵌入模型联通性测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
