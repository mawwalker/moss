import asyncio
import websockets
import json
import numpy as np
from typing import Callable, Optional
from loguru import logger
from core.audio_manager import AsyncAudioConsumer
from utils.audio_utils import audio_array_to_bytes


class AsyncSpeechRecognizer(AsyncAudioConsumer):
    """异步实时语音识别器 - 基于统一音频管理器"""
    
    def __init__(self, audio_manager, 
                 websocket_uri: str = "ws://localhost:8000/sttRealtime"):
        super().__init__(audio_manager)
        
        self.websocket_uri = websocket_uri
        self.websocket = None
        self.is_recognizing = False
        self.result_callback = None
        self.current_idx = 0
        self.accumulated_text = ""
        
        # WebSocket 发送队列
        self.send_queue = None
        self.send_task = None
        
        logger.info("Async speech recognizer initialized")
        
    def set_result_callback(self, callback: Callable[[str, bool], None]):
        """设置结果回调函数
        
        Args:
            callback: 回调函数，参数为 (text, is_final)
                     text: 识别的文本
                     is_final: 是否为最终结果（idx增加表示句子结束）
        """
        self.result_callback = callback
        
    async def connect(self) -> bool:
        """连接到WebSocket服务器"""
        try:
            self.websocket = await websockets.connect(self.websocket_uri)
            logger.info(f"Connected to STT service: {self.websocket_uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to STT service: {e}")
            return False
            
    async def disconnect(self):
        """断开连接"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            logger.info("Disconnected from STT service")
            
    async def start_recognition(self) -> bool:
        """开始语音识别"""
        logger.info("Starting speech recognition...")
        
        # 连接WebSocket
        if not await self.connect():
            return False
            
        # 重置状态
        self.is_recognizing = True
        self.current_idx = 0
        self.accumulated_text = ""
        
        # 创建发送队列
        self.send_queue = asyncio.Queue()
        
        try:
            # 启动发送和接收任务
            self.send_task = asyncio.create_task(self._sending_loop())
            receiving_task = asyncio.create_task(self._receiving_loop())
            
            # 开始消费音频数据
            await self.start_consuming()
            
            logger.info("Speech recognition started, waiting for results...")
            
            # 等待接收任务完成（通常在停止识别时）
            await receiving_task
            
            return True
            
        except Exception as e:
            logger.error(f"Speech recognition failed: {e}")
            return False
        finally:
            await self._cleanup()
            
    async def stop_recognition(self):
        """停止语音识别"""
        logger.info("Stopping speech recognition...")
        
        self.is_recognizing = False
        
        # 停止音频消费
        await self.stop_consuming()
        
        # 清理资源
        await self._cleanup()
        
    async def _cleanup(self):
        """清理资源"""
        # 停止发送任务
        if self.send_task:
            self.send_task.cancel()
            try:
                await self.send_task
            except asyncio.CancelledError:
                pass
            self.send_task = None
            
        # 清理发送队列
        if self.send_queue:
            while not self.send_queue.empty():
                try:
                    self.send_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
            self.send_queue = None
            
        # 断开连接
        await self.disconnect()
        
    async def on_audio_chunk(self, audio_data: np.ndarray):
        """处理音频数据块"""
        if not self.is_recognizing or not self.send_queue:
            return
            
        try:
            # 将音频数据转换为字节并放入发送队列
            audio_bytes = audio_array_to_bytes(audio_data)
            await self.send_queue.put(audio_bytes)
        except Exception as e:
            logger.error(f"Error processing audio chunk for STT: {e}")
            
    async def _sending_loop(self):
        """发送音频数据循环"""
        try:
            while self.is_recognizing:
                if not self.send_queue:
                    await asyncio.sleep(0.1)
                    continue
                    
                try:
                    # 从队列获取音频数据
                    audio_bytes = await asyncio.wait_for(
                        self.send_queue.get(), timeout=0.5
                    )
                    
                    # 发送到WebSocket
                    if self.websocket:
                        await self.websocket.send(audio_bytes)
                    
                except asyncio.TimeoutError:
                    # 超时没有数据，继续循环
                    continue
                except Exception as e:
                    logger.error(f"Error sending audio data: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Sending loop error: {e}")
            
    async def _receiving_loop(self):
        """接收识别结果循环"""
        try:
            while self.is_recognizing:
                if not self.websocket:
                    await asyncio.sleep(0.1)
                    continue
                    
                try:
                    # 接收WebSocket消息
                    message = await asyncio.wait_for(
                        self.websocket.recv(), timeout=0.5
                    )
                    
                    # 解析结果
                    await self._process_recognition_result(message)
                    
                except asyncio.TimeoutError:
                    # 超时没有消息，继续循环
                    continue
                except websockets.exceptions.ConnectionClosed:
                    logger.info("WebSocket connection closed")
                    break
                except Exception as e:
                    logger.error(f"Error receiving recognition result: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Receiving loop error: {e}")
            
    async def _process_recognition_result(self, message):
        """处理识别结果"""
        try:
            result = json.loads(message)
            
            # 提取结果信息
            text = result.get("text", "")
            idx = result.get("idx", 0)
            
            # 检查是否为最终结果（idx增加表示句子结束）
            is_final = idx > self.current_idx
            
            if is_final:
                self.current_idx = idx
                self.accumulated_text = text
            else:
                # 临时结果，更新当前文本
                self.accumulated_text = text
                
            # 调用回调函数
            if self.result_callback and text:
                self.result_callback(text, is_final)
                
            if is_final:
                logger.info(f"Final recognition result: {text}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse recognition result: {e}")
        except Exception as e:
            logger.error(f"Error processing recognition result: {e}")


class QuestionCollector:
    """问题收集器 - 收集完整的用户问题"""
    
    def __init__(self, silence_timeout: float = 1.5, min_question_length: int = 3):
        self.silence_timeout = silence_timeout  # 静音超时时间 - 减少到1.5秒
        self.min_question_length = min_question_length  # 最小问题长度
        
        self.current_question = ""
        self.last_update_time = 0
        self.is_collecting = False
        self.async_question_callback = None
        
        # 静音检测任务
        self.silence_task = None
        
        logger.info(f"Question collector initialized (timeout={silence_timeout}s, min_length={min_question_length})")
        
    def set_async_question_callback(self, callback):
        """设置异步问题收集回调"""
        self.async_question_callback = callback
        
    def reset(self):
        """重置收集器状态"""
        self.current_question = ""
        self.last_update_time = 0
        self.is_collecting = False
        
        # 取消静音检测任务
        if self.silence_task:
            self.silence_task.cancel()
            self.silence_task = None
            
        logger.info("Question collector reset")
        
    def on_stt_result(self, text: str, is_final: bool):
        """处理STT结果"""
        import time
        
        if not text.strip():
            return
            
        self.current_question = text.strip()
        self.last_update_time = time.time()
        
        if not self.is_collecting:
            self.is_collecting = True
            logger.info("Started collecting question...")
            
        # 如果是最终结果且长度足够，立即触发回调
        if is_final and len(self.current_question) >= self.min_question_length:
            logger.info(f"Question finalized by STT: {self.current_question}")
            self._trigger_question_callback()
            return
            
        # 重启静音检测任务
        if self.silence_task:
            self.silence_task.cancel()
            
        self.silence_task = asyncio.create_task(self._silence_detection())
        
    async def _silence_detection(self):
        """静音检测"""
        try:
            await asyncio.sleep(self.silence_timeout)
            
            # 检查是否有足够长的问题
            if (self.is_collecting and 
                len(self.current_question) >= self.min_question_length):
                
                logger.info(f"Question finalized by silence: {self.current_question}")
                self._trigger_question_callback()
                
        except asyncio.CancelledError:
            pass  # 任务被取消，正常情况
        except Exception as e:
            logger.error(f"Error in silence detection: {e}")
            
    def _trigger_question_callback(self):
        """触发问题回调"""
        question = self.current_question
        self.reset()
        
        if self.async_question_callback:
            # 创建任务来调用异步回调
            asyncio.create_task(self.async_question_callback(question))
            
    def get_current_question(self) -> str:
        """获取当前问题"""
        return self.current_question
