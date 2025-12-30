import os
import time
import threading
from typing import List, Optional, Tuple
from datetime import datetime, timedelta
from openai import OpenAI, OpenAIError
from src.config.manager import ConfigManager
from src.common.logger import get_logger


class RateLimiter:
    """速率限制器，控制RPM（每分钟请求数）和TPM（每分钟令牌数）"""
    
    def __init__(self, rpm: int = 10, tpm: int = 10000, enable_adaptive_delay: bool = True, initial_delay: float = 0.5):
        self.rpm = rpm
        self.tpm = tpm
        self.enable_adaptive_delay = enable_adaptive_delay
        self.initial_delay = initial_delay
        
        # 请求历史记录
        self.request_times = []
        self.token_counts = []
        self.lock = threading.RLock()
        
        # 自适应延迟参数
        self.current_delay = initial_delay
        self.min_delay = 0.1
        self.max_delay = 5.0
        self.backoff_factor = 1.5
        self.recovery_factor = 0.9
    
    def _clean_old_records(self):
        """清理一分钟前的记录"""
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        self.request_times = [t for t in self.request_times if t > one_minute_ago]
        self.token_counts = [t for t in self.token_counts if t[0] > one_minute_ago]
    
    def _get_current_rpm(self) -> float:
        """计算当前RPM"""
        self._clean_old_records()
        return len(self.request_times)
    
    def _get_current_tpm(self) -> int:
        """计算当前TPM"""
        self._clean_old_records()
        one_minute_ago = datetime.now() - timedelta(minutes=1)
        return sum(tokens for timestamp, tokens in self.token_counts if timestamp > one_minute_ago)
    
    def _estimate_tokens(self, text: str) -> int:
        """估算文本的令牌数（简单估算，中文大约2字符=1个token）"""
        # 对于中文，使用简单估算：1个汉字约等于1.3个token，标点和空格等忽略
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        # 对于英文字母和数字
        other_chars = len(text) - chinese_chars
        # 估算：中文字符*1.3 + 其他字符*0.25
        estimated = int(chinese_chars * 1.3 + other_chars * 0.25)
        return max(estimated, 1)
    
    def wait_if_needed(self, texts: List[str]) -> float:
        """
        如果需要等待以满足速率限制，则进行等待
        返回实际等待的时间（秒）
        """
        with self.lock:
            self._clean_old_records()
            
            # 估算总令牌数
            total_tokens = sum(self._estimate_tokens(text) for text in texts)
            
            # 检查是否超过限制
            current_rpm = self._get_current_rpm()
            current_tpm = self._get_current_tpm()
            
            # 如果启用自适应延迟，根据当前负载调整延迟
            if self.enable_adaptive_delay:
                rpm_ratio = current_rpm / max(self.rpm, 1)
                tpm_ratio = current_tpm / max(self.tpm, 1)
                
                if rpm_ratio > 0.8 or tpm_ratio > 0.8:
                    # 接近限制，增加延迟
                    self.current_delay = min(self.current_delay * self.backoff_factor, self.max_delay)
                elif rpm_ratio < 0.5 and tpm_ratio < 0.5:
                    # 负载较低，减少延迟
                    self.current_delay = max(self.current_delay * self.recovery_factor, self.min_delay)
            
            # 计算需要的等待时间
            wait_time = 0.0
            
            # 检查RPM限制
            if current_rpm >= self.rpm:
                # 需要等待直到有请求槽位
                oldest_time = min(self.request_times) if self.request_times else datetime.now()
                time_since_oldest = (datetime.now() - oldest_time).total_seconds()
                wait_time = max(wait_time, 60 - time_since_oldest)
            
            # 检查TPM限制
            if current_tpm + total_tokens > self.tpm:
                # 需要等待直到令牌重置
                if self.token_counts:
                    oldest_token_time = min(timestamp for timestamp, _ in self.token_counts)
                    time_since_oldest = (datetime.now() - oldest_token_time).total_seconds()
                    wait_time = max(wait_time, 60 - time_since_oldest)
            
            # 添加基本延迟
            wait_time += self.current_delay
            
            # 执行等待
            if wait_time > 0:
                time.sleep(wait_time)
            
            # 记录请求
            now = datetime.now()
            self.request_times.append(now)
            self.token_counts.append((now, total_tokens))
            
            return wait_time


class EmbeddingNode:
    """嵌入节点：调用OpenAI兼容API生成文本向量（带速率限制的批处理）"""

    def __init__(self, config: ConfigManager = None):
        self.config = config or ConfigManager()
        self.client = self._init_client()
        self._dimension = self.config.vector_dim
        self._model = self.config.embedding_model
        self.logger = get_logger('tag_rag.embedding')
        
        # 初始化速率限制器
        self.rate_limiter = RateLimiter(
            rpm=self.config.embedding_rpm,
            tpm=self.config.embedding_tpm,
            enable_adaptive_delay=self.config.embedding_enable_adaptive_delay,
            initial_delay=self.config.embedding_request_delay
        )
        
        # 根据API限制调整批处理大小
        # SiliconFlow API: 每个请求最多512个tokens，最大batch_size为16
        self.max_batch_size = min(self.config.batch_size, 16)  # 最大16个文本/请求
        self.max_tokens_per_request = 512  # SiliconFlow免费账户限制

    def _init_client(self) -> OpenAI:
        """初始化OpenAI客户端（兼容其他OpenAI兼容API）"""
        # 优先从配置读取API密钥
        api_key = self.config.embedding_api_key
        if not api_key:
            # 如果配置中没有，尝试从环境变量读取
            api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("未设置OpenAI API密钥：请在配置文件中配置 embedding.api_key（优先）或设置环境变量 OPENAI_API_KEY")

        base_url = self.config.embedding_api_base
        return OpenAI(api_key=api_key, base_url=base_url)

    def _create_batches(self, texts: List[str]) -> List[List[str]]:
        """根据令牌限制创建批处理"""
        batches = []
        current_batch = []
        current_tokens = 0
        
        for text in texts:
            text_tokens = self.rate_limiter._estimate_tokens(text)
            
            # 如果单个文本超过限制，需要单独处理
            if text_tokens > self.max_tokens_per_request:
                # 当前批处理先保存
                if current_batch:
                    batches.append(current_batch)
                    current_batch = []
                    current_tokens = 0
                # 单个文本作为一批
                batches.append([text])
                continue
            
            # 检查是否可以将文本加入当前批处理
            if (len(current_batch) >= self.max_batch_size or 
                current_tokens + text_tokens > self.max_tokens_per_request):
                # 当前批处理已满，保存并开始新批处理
                if current_batch:
                    batches.append(current_batch)
                current_batch = [text]
                current_tokens = text_tokens
            else:
                # 添加到当前批处理
                current_batch.append(text)
                current_tokens += text_tokens
        
        # 添加最后一个批处理
        if current_batch:
            batches.append(current_batch)
        
        return batches

    def _embed_batch(self, texts: List[str], max_retries: int = 3) -> List[List[float]]:
        """处理单个批次的文本"""
        for attempt in range(max_retries):
            try:
                # 构建请求参数
                params = {
                    "model": self._model,
                    "input": texts,
                    "encoding_format": "float"
                }
                # 如果配置的维度不是默认值，传递dimensions参数
                # 注意：某些模型可能不支持dimensions参数，但SiliconFlow的API需要
                if self._dimension is not None:
                    params["dimensions"] = self._dimension
                
                response = self.client.embeddings.create(**params)
                embeddings = [item.embedding for item in response.data]
                
                # 验证维度
                for i, embedding in enumerate(embeddings):
                    if len(embedding) != self._dimension:
                        raise ValueError(
                            f"嵌入维度不匹配（文本{i}）: 期望 {self._dimension}, 实际 {len(embedding)}"
                        )
                
                return embeddings
            except OpenAIError as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = 2 ** attempt  # 指数退避
                time.sleep(wait_time)
                continue

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成向量（带速率限制）"""
        if not texts:
            return []
        
        # 根据令牌限制创建批处理
        batches = self._create_batches(texts)
        
        results = []
        total_wait_time = 0
        
        for i, batch in enumerate(batches):
            # 应用速率限制
            wait_time = self.rate_limiter.wait_if_needed(batch)
            total_wait_time += wait_time
            
            # 处理当前批次
            try:
                embeddings = self._embed_batch(batch)
                results.extend(embeddings)
            except Exception as e:
                # 如果单个批次失败，记录错误但继续处理其他批次
                self.logger.error(f"批次 {i+1}/{len(batches)} 处理失败: {e}")
                # 为失败的批次添加空向量占位符
                results.extend([None] * len(batch))
        
        if total_wait_time > 0:
            self.logger.info(f"速率限制等待总时间: {total_wait_time:.2f}秒")
        
        return results

    def process(self, texts: List[str]) -> List[List[float]]:
        """处理一批文本，返回向量列表"""
        return self.embed_batch(texts)

    def get_dimension(self) -> int:
        """返回嵌入维度"""
        return self._dimension
