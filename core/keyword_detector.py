import asyncio
import numpy as np
import sherpa_onnx
from pathlib import Path
from typing import Callable, Optional
from loguru import logger
from core.audio_manager import AsyncAudioConsumer



class AsyncKeywordDetector(AsyncAudioConsumer):
    """异步关键词检测器 - 基于统一音频管理器"""
    
    def __init__(self, audio_manager, 
                 tokens_path: str = "assets/sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01/tokens.txt",
                 encoder_path: str = "assets/sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01/encoder-epoch-99-avg-1-chunk-16-left-64.onnx",
                 decoder_path: str = "assets/sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01/decoder-epoch-99-avg-1-chunk-16-left-64.onnx",
                 joiner_path: str = "assets/sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01/joiner-epoch-99-avg-1-chunk-16-left-64.onnx",
                 keywords_file: str = "assets/keywords_zh.txt",
                 keywords_score: float = 2.0,
                 keywords_threshold: float = 0.15,
                 **kwargs):
        
        super().__init__(audio_manager)
        
        self.sample_rate = audio_manager.sample_rate
        self.async_callback = None
        
        # 验证文件存在
        for file_path in [tokens_path, encoder_path, decoder_path, joiner_path, keywords_file]:
            if not Path(file_path).exists():
                raise FileNotFoundError(f"Required file not found: {file_path}")
        
        # 初始化关键词检测器
        self.keyword_spotter = sherpa_onnx.KeywordSpotter(
            tokens=tokens_path,
            encoder=encoder_path,
            decoder=decoder_path,
            joiner=joiner_path,
            num_threads=1,
            max_active_paths=4,
            keywords_file=keywords_file,
            keywords_score=keywords_score,
            keywords_threshold=keywords_threshold,
            num_trailing_blanks=1,
            provider="cpu",
        )
        
        # 创建检测流
        self.stream = self.keyword_spotter.create_stream()
        
        logger.info("Async keyword detector initialized")
        
    def set_async_keyword_callback(self, async_callback):
        """设置异步关键词检测回调函数"""
        self.async_callback = async_callback
        
    async def start_detection(self):
        """开始关键词检测"""
        logger.info("Starting keyword detection...")
        await self.start_consuming()
        logger.info("Keyword detection started")
        
    async def stop_detection(self):
        """停止关键词检测"""
        logger.info("Stopping keyword detection...")
        await self.stop_consuming()
        logger.info("Keyword detection stopped")
        
    async def on_audio_chunk(self, audio_data: np.ndarray):
        """处理音频数据块"""
        try:
            # 将音频数据送入关键词检测器
            self.stream.accept_waveform(self.sample_rate, audio_data)
            
            # 检查是否有检测结果
            while self.keyword_spotter.is_ready(self.stream):
                self.keyword_spotter.decode_stream(self.stream)
                result = self.keyword_spotter.get_result(self.stream)
                
                if result:
                    logger.info(f"Keyword detected: {result}")
                    
                    # 调用异步回调
                    if self.async_callback:
                        await self.async_callback(result)
                    
                    # 重置流以准备下次检测
                    self.keyword_spotter.reset_stream(self.stream)
                    
        except Exception as e:
            logger.error(f"Error processing audio for keyword detection: {e}")
