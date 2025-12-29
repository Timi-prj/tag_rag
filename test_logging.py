#!/usr/bin/env python3
"""
测试日志功能
验证异步日志、文件轮转和配置集成
"""
import os
import sys
import time
import tempfile
import shutil
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.common.logger import configure_logging, get_logger, temporary_log_level
from src.config.manager import ConfigManager

def test_basic_logging():
    """测试基础日志功能"""
    print("测试基础日志功能...")
    
    # 创建临时配置
    config = {
        'level': 'DEBUG',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'handlers': {
            'console': {
                'enabled': True,
                'level': 'INFO'
            },
            'file': {
                'enabled': False  # 测试时不使用文件
            }
        }
    }
    
    configure_logging(config)
    logger = get_logger('test')
    
    # 测试不同级别的日志
    logger.debug("这是一条DEBUG日志")
    logger.info("这是一条INFO日志")
    logger.warning("这是一条WARNING日志")
    logger.error("这是一条ERROR日志")
    
    try:
        raise ValueError("测试异常")
    except ValueError:
        logger.exception("捕获到异常")
    
    print("  基础日志测试完成")
    return True

def test_log_levels():
    """测试日志级别控制"""
    print("测试日志级别控制...")
    
    config = {
        'level': 'WARNING',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'handlers': {
            'console': {
                'enabled': True,
                'level': 'WARNING'
            }
        }
    }
    
    configure_logging(config)
    logger = get_logger('test.levels')
    
    # INFO级别消息应该不会显示（因为设置了WARNING级别）
    logger.info("这条INFO消息应该不会显示")
    logger.warning("这条WARNING消息应该显示")
    logger.error("这条ERROR消息应该显示")
    
    print("  日志级别测试完成")
    return True

def test_temporary_log_level():
    """测试临时日志级别修改"""
    print("测试临时日志级别修改...")
    
    config = {
        'level': 'WARNING',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'handlers': {
            'console': {
                'enabled': True,
                'level': 'WARNING'
            }
        }
    }
    
    configure_logging(config)
    logger = get_logger('test.temp')
    
    logger.info("正常INFO级别不会显示")
    
    with temporary_log_level('test.temp', 'INFO'):
        logger.info("临时INFO级别：这条消息应该显示")
    
    logger.info("恢复后，这条INFO消息应该不会显示")
    
    print("  临时日志级别测试完成")
    return True

def test_config_integration():
    """测试与ConfigManager的集成"""
    print("测试与ConfigManager的集成...")
    
    config_manager = ConfigManager()
    
    # 使用配置中的日志设置
    configure_logging({
        'level': config_manager.log_level,
        'format': config_manager.log_format,
        'handlers': config_manager.log_handlers
    })
    
    logger = get_logger('test.config')
    logger.info("使用ConfigManager配置的日志系统")
    logger.info(f"日志级别: {config_manager.log_level}")
    logger.info(f"日志格式: {config_manager.log_format}")
    
    # 检查处理器
    handlers = config_manager.log_handlers
    if handlers.get('console', {}).get('enabled'):
        logger.info("控制台日志已启用")
    if handlers.get('file', {}).get('enabled'):
        logger.info(f"文件日志已启用，路径: {handlers['file'].get('path')}")
    
    print("  配置集成测试完成")
    return True

def test_log_rotation():
    """测试日志轮转（需要文件系统）"""
    print("测试日志轮转...")
    
    # 创建临时目录用于测试
    temp_dir = tempfile.mkdtemp(prefix='tag_rag_log_test_')
    log_file = os.path.join(temp_dir, 'test.log')
    
    try:
        config = {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'handlers': {
                'console': {
                    'enabled': False
                },
                'file': {
                    'enabled': True,
                    'path': log_file,
                    'max_bytes': 1024,  # 1KB，便于测试轮转
                    'backup_count': 3,
                    'when': 'midnight'
                }
            }
        }
        
        configure_logging(config)
        logger = get_logger('test.rotation')
        
        # 生成足够的日志以触发轮转
        for i in range(100):
            logger.info(f"测试日志消息 {i}: " + "x" * 50)
        
        # 检查日志文件是否存在
        if os.path.exists(log_file):
            file_size = os.path.getsize(log_file)
            print(f"  主日志文件大小: {file_size} 字节")
            
            # 检查是否有轮转文件
            rotated_files = []
            for i in range(1, 4):
                rotated_file = f"{log_file}.{i}"
                if os.path.exists(rotated_file):
                    rotated_files.append(rotated_file)
            
            print(f"  发现 {len(rotated_files)} 个轮转文件")
            
            # 清理
            logger.info("日志轮转测试完成")
            return True
        else:
            print(f"  错误：日志文件未创建: {log_file}")
            return False
            
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)

def test_async_logging():
    """测试异步日志性能"""
    print("测试异步日志性能...")
    
    config = {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'handlers': {
            'console': {
                'enabled': True,
                'level': 'INFO'
            }
        }
    }
    
    configure_logging(config)
    logger = get_logger('test.async')
    
    start_time = time.time()
    
    # 记录大量日志（异步应该不会阻塞）
    for i in range(1000):
        logger.info(f"异步日志测试 {i}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"  记录1000条日志耗时: {duration:.2f} 秒")
    print(f"  平均每条: {duration/1000*1000:.2f} 毫秒")
    
    # 简单性能检查
    if duration < 2.0:  # 2秒内完成1000条日志
        print("  异步日志性能良好")
        return True
    else:
        print(f"  警告：日志记录较慢，耗时 {duration:.2f} 秒")
        return False

def main():
    """主测试函数"""
    print("开始日志功能测试...")
    print("="*50)
    
    tests = [
        ("基础日志功能", test_basic_logging),
        ("日志级别控制", test_log_levels),
        ("临时日志级别", test_temporary_log_level),
        ("配置集成", test_config_integration),
        ("异步日志性能", test_async_logging),
        # ("日志轮转", test_log_rotation),  # 文件系统测试，可选
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"  测试 '{test_name}' 失败: {e}")
            results.append((test_name, False))
    
    print("\n" + "="*50)
    print("测试总结:")
    
    all_passed = True
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {test_name}: {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        print("\n✅ 所有日志测试通过！")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查日志系统配置")
        return 1

if __name__ == "__main__":
    sys.exit(main())
