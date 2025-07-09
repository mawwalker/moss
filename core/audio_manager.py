import asyncio
import threading
import sounddevice as sd
import numpy as np
from typing import Callable, List, Optional
from loguru import logger
from utils.audio_utils import AudioRecorder


class AudioManager:
    """统一音频管理器 - 管理单一音频流，分发给多个消费者"""
    
    def __init__(self, sample_rate: int = 16000, chunk_size: float = 0.1):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size  # 每次读取的时间长度（秒）
        self.samples_per_read = int(chunk_size * sample_rate)
        
        # 音频流管理
        self.audio_stream = None
        self.is_running = False
        self.audio_recorder = AudioRecorder(sample_rate=sample_rate)
        
        # 消费者管理
        self.consumers = []  # 音频数据消费者列表
        self._consumer_lock = threading.Lock()
        
        # 线程安全的事件循环
        self._loop = None
        self._stream_thread = None
        
        logger.info(f"Audio manager initialized (sample_rate={sample_rate}, chunk_size={chunk_size}s)")
        
    def add_consumer(self, consumer: Callable[[np.ndarray], None]) -> int:
        """添加音频数据消费者
        
        Args:
            consumer: 消费者函数，接收音频数据（numpy数组）
            
        Returns:
            consumer_id: 消费者ID，用于后续移除
        """
        with self._consumer_lock:
            consumer_id = len(self.consumers)
            self.consumers.append(consumer)
            logger.info(f"Added audio consumer {consumer_id}, total consumers: {len(self.consumers)}")
            return consumer_id
            
    def remove_consumer(self, consumer_id: int):
        """移除音频数据消费者
        
        Args:
            consumer_id: 消费者ID
        """
        with self._consumer_lock:
            if 0 <= consumer_id < len(self.consumers):
                self.consumers[consumer_id] = None  # 标记为已移除
                logger.info(f"Removed audio consumer {consumer_id}")
            else:
                logger.warning(f"Invalid consumer ID: {consumer_id}")
                
    def _distribute_audio_data(self, audio_data: np.ndarray):
        """分发音频数据给所有消费者"""
        with self._consumer_lock:
            active_consumers = [c for c in self.consumers if c is not None]
            
        for consumer in active_consumers:
            try:
                consumer(audio_data.copy())  # 传递数据副本，避免修改原始数据
            except Exception as e:
                logger.error(f"Error in audio consumer: {e}")
                
    def start_stream(self) -> bool:
        """启动音频流"""
        if self.is_running:
            logger.warning("Audio stream is already running")
            return True
            
        if not self.audio_recorder.setup():
            logger.error("Failed to setup audio recorder")
            return False
            
        try:
            self.is_running = True
            self._loop = asyncio.new_event_loop()
            
            # 在独立线程中运行音频流
            self._stream_thread = threading.Thread(target=self._run_stream_thread, daemon=True)
            self._stream_thread.start()
            
            logger.info("Audio stream started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start audio stream: {e}")
            self.is_running = False
            return False
            
    def stop_stream(self):
        """停止音频流"""
        if not self.is_running:
            return
            
        logger.info("Stopping audio stream...")
        self.is_running = False
        
        # 等待流线程结束
        if self._stream_thread and self._stream_thread.is_alive():
            self._stream_thread.join(timeout=5.0)
            
        # 清理
        self.consumers.clear()
        
        logger.info("Audio stream stopped")
        
    def _run_stream_thread(self):
        """在独立线程中运行音频流"""
        asyncio.set_event_loop(self._loop)
        
        try:
            self._loop.run_until_complete(self._stream_loop())
        except Exception as e:
            logger.error(f"Audio stream thread error: {e}")
        finally:
            self._loop.close()
            
    async def _stream_loop(self):
        """音频流主循环"""
        try:
            with sd.InputStream(
                channels=1,
                dtype="float32", 
                samplerate=self.sample_rate,
                device=self.audio_recorder.device_id,
                blocksize=self.samples_per_read
            ) as stream:
                
                logger.info(f"Audio stream started on device {self.audio_recorder.device_id}")
                
                while self.is_running:
                    try:
                        # 读取音频数据
                        audio_data, overflowed = stream.read(self.samples_per_read)
                        
                        if overflowed:
                            logger.warning("Audio buffer overflow detected")
                            
                        # 确保数据格式正确
                        audio_data = audio_data.reshape(-1).astype(np.float32)
                        
                        # 分发给所有消费者
                        self._distribute_audio_data(audio_data)
                        
                        # 短暂等待，避免过度占用CPU
                        await asyncio.sleep(0.001)
                        
                    except Exception as e:
                        logger.error(f"Error in audio stream loop: {e}")
                        break
                        
        except Exception as e:
            logger.error(f"Failed to create audio stream: {e}")
            
        logger.info("Audio stream loop ended")
        
    def get_stream_info(self) -> dict:
        """获取音频流信息"""
        return {
            "is_running": self.is_running,
            "sample_rate": self.sample_rate,
            "chunk_size": self.chunk_size,
            "samples_per_read": self.samples_per_read,
            "active_consumers": len([c for c in self.consumers if c is not None]),
            "device_id": self.audio_recorder.device_id if self.audio_recorder else None
        }


class AsyncAudioConsumer:
    """异步音频消费者基类"""
    
    def __init__(self, audio_manager: AudioManager):
        self.audio_manager = audio_manager
        self.consumer_id = None
        self.audio_queue = None
        self.processing_task = None
        
    async def start_consuming(self):
        """开始消费音频数据"""
        if self.consumer_id is not None:
            logger.warning("Audio consumer is already started")
            return
            
        # 创建音频队列
        self.audio_queue = asyncio.Queue(maxsize=100)  # 限制队列大小防止内存泄漏
        
        # 注册为音频消费者
        self.consumer_id = self.audio_manager.add_consumer(self._on_audio_data)
        
        # 启动处理任务
        self.processing_task = asyncio.create_task(self._process_audio())
        
        logger.info(f"Started async audio consumer {self.consumer_id}")
        
    async def stop_consuming(self):
        """停止消费音频数据"""
        if self.consumer_id is None:
            return
            
        # 移除消费者
        self.audio_manager.remove_consumer(self.consumer_id)
        self.consumer_id = None
        
        # 停止处理任务
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
            self.processing_task = None
            
        # 清理队列
        if self.audio_queue:
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
            self.audio_queue = None
            
        logger.info("Stopped async audio consumer")
        
    def _on_audio_data(self, audio_data: np.ndarray):
        """音频数据回调（在音频线程中调用）"""
        if self.audio_queue is None:
            return
            
        try:
            self.audio_queue.put_nowait(audio_data)
        except asyncio.QueueFull:
            # 队列满了，丢弃最旧的数据
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.put_nowait(audio_data)
            except asyncio.QueueEmpty:
                pass
                
    async def _process_audio(self):
        """处理音频数据（子类需要重写此方法）"""
        while True:
            try:
                audio_data = await self.audio_queue.get()
                await self.on_audio_chunk(audio_data)
                self.audio_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing audio chunk: {e}")
                
    async def on_audio_chunk(self, audio_data: np.ndarray):
        """处理单个音频块（子类需要重写此方法）"""
        raise NotImplementedError("Subclass must implement on_audio_chunk method")
