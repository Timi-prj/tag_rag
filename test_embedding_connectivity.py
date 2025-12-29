#!/usr/bin/env python3
"""
测试嵌入模型联通性
检查配置的API端点是否可达，以及模型是否有效
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
    
    env_key = os.environ.get("OPENAI_API_KEY")
    print(f"  环境变量OPENAI_API_KEY: {'已设置' if env_key else '未设置'}")
    
    # 确定最终使用的API密钥
    final_key = env_key or config.embedding_api_key
    print(f"  最终使用的API密钥: {'已设置' if final_key else '未设置'}")
    
    return config, final_key

def test_network_connectivity(config):
    """测试网络连通性（不依赖API密钥）"""
    print("\n测试网络连通性...")
    try:
        # 尝试连接API基础URL（GET请求）
        response = requests.get(config.embedding_api_base, timeout=10)
        print(f"  连接到 {config.embedding_api_base} 成功，状态码: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"  连接失败：无法连接到 {config.embedding_api_base}，请检查网络或URL")
        return False
    except requests.exceptions.Timeout:
        print(f"  连接超时：{config.embedding_api_base} 响应超时")
        return False
    except Exception as e:
        print(f"  连接异常: {e}")
        return False

def test_embedding_endpoint(config, api_key):
    """测试嵌入端点（使用API密钥）"""
    print("\n测试嵌入端点...")
    
    if not api_key:
        print("  未提供API密钥，跳过嵌入端点测试")
        return False
    
    # 构建请求头
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # 请求数据
    data = {
        "model": config.embedding_model,
        "input": "测试连通性",
        "encoding_format": "float"
    }
    
    # 确定端点URL
    endpoint = config.embedding_api_base.rstrip('/') + "/embeddings"
    print(f"  请求端点: {endpoint}")
    print(f"  使用模型: {config.embedding_model}")
    
    try:
        response = requests.post(endpoint, headers=headers, json=data, timeout=30)
        print(f"  响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("  ✅ 嵌入API测试成功！")
            result = response.json()
            print(f"    返回向量维度: {len(result['data'][0]['embedding'])}")
            return True
        elif response.status_code == 401:
            print("  ❌ 认证失败：API密钥无效")
            return False
        elif response.status_code == 404:
            print("  ❌ 端点不存在：请检查API Base URL")
            return False
        else:
            print(f"  ❌ 请求失败，状态码: {response.status_code}")
            print(f"     响应内容: {response.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        print("  ❌ 连接错误：无法连接到嵌入端点")
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
        return True
    except ValueError as e:
        print(f"  ❌ EmbeddingNode初始化失败（缺少API密钥）: {e}")
        return False
    except Exception as e:
        print(f"  ❌ EmbeddingNode初始化异常: {e}")
        return False

def main():
    print("开始嵌入模型联通性测试...")
    
    # 检查配置
    config, api_key = test_config()
    
    # 测试网络连通性
    network_ok = test_network_connectivity(config)
    
    # 如果有API密钥，测试嵌入端点
    endpoint_ok = False
    if api_key:
        endpoint_ok = test_embedding_endpoint(config, api_key)
    else:
        print("\n⚠️  未设置API密钥，无法测试嵌入端点")
    
    # 测试EmbeddingNode初始化
    node_ok = test_embedding_node()
    
    print("\n" + "="*50)
    print("测试总结:")
    print(f"  网络连通性: {'✅ 通过' if network_ok else '❌ 失败'}")
    print(f"  嵌入端点: {'✅ 通过' if endpoint_ok else ('❌ 失败' if api_key else '⚠️ 跳过')}")
    print(f"  EmbeddingNode初始化: {'✅ 通过' if node_ok else '❌ 失败'}")
    
    if not api_key:
        print("\n⚠️  建议:")
        print("  1. 设置环境变量 OPENAI_API_KEY")
        print("  2. 或在 config.yaml 中配置 embedding.api_key")
        print("  这样才能使用嵌入功能")
    
    if network_ok and node_ok:
        print("\n✅ 基本配置正确，嵌入模块可正常工作（需提供有效API密钥）")
        return 0
    else:
        print("\n❌ 配置或网络存在问题，请检查上述错误")
        return 1

if __name__ == "__main__":
    sys.exit(main())
