import asyncio
import websockets
import json
import numpy as np
import sounddevice as sd
from typing import Callable, Optional
from loguru import logger
from utils.audio_utils import AudioRecorder, audio_array_to_bytes


class SpeechRecognizer:
    """实时语音识别器"""
    
    def __init__(self, 
                 websocket_uri: str = "ws://localhost:8000/sttRealtime",
                 sample_rate: int = 16000):
        self.websocket_uri = websocket_uri
        self.sample_rate = sample_rate
        self.websocket = None
        self.is_recording = False
        self.audio_recorder = AudioRecorder(sample_rate=sample_rate)
        self.result_callback = None
        self.current_idx = 0
        self.accumulated_text = ""
        
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
        logger.info("Attempting to start speech recognition...")
        
        if not await self.connect():
            logger.error("Failed to connect to STT service")
            return False
            
        if not self.audio_recorder.setup():
            logger.error("Failed to setup audio recorder")
            return False
            
        self.is_recording = True
        self.current_idx = 0
        self.accumulated_text = ""
        
        logger.info("Starting recording and receiving tasks...")
        
        # 启动录音和接收结果的任务
        recording_task = asyncio.create_task(self._recording_loop())
        receiving_task = asyncio.create_task(self._receiving_loop())
        
        try:
            await asyncio.gather(recording_task, receiving_task)
            return True
        except Exception as e:
            logger.error(f"Speech recognition failed: {e}")
            return False
        finally:
            self.is_recording = False
            
    def stop_recognition(self):
        """停止语音识别"""
        self.is_recording = False
        logger.info("Speech recognition stopped")
        
    async def _recording_loop(self):
        """录音循环"""
        samples_per_read = int(0.1 * self.sample_rate)  # 100ms
        
        with sd.InputStream(
            channels=1,
            dtype="float32",
            samplerate=self.sample_rate,
            device=self.audio_recorder.device_id
        ) as audio_stream:
            
            logger.info("Started audio recording for STT")
            
            while self.is_recording:
                try:
                    samples, _ = audio_stream.read(samples_per_read)
                    samples = samples.reshape(-1)
                    
                    # 转换为字节并发送
                    audio_bytes = audio_array_to_bytes(samples)
                    if self.websocket:
                        await self.websocket.send(audio_bytes)
                        
                except Exception as e:
                    logger.error(f"Error in recording loop: {e}")
                    break
                    
    async def _receiving_loop(self):
        """接收识别结果循环"""
        while self.is_recording and self.websocket:
            try:
                response = await asyncio.wait_for(
                    self.websocket.recv(), timeout=1.0
                )
                
                try:
                    result = json.loads(response)
                    await self._process_result(result)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse STT result: {response}")
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error receiving STT result: {e}")
                break
                
    async def _process_result(self, result: dict):
        """处理识别结果"""
        if "text" in result and "idx" in result:
            text = result["text"]
            idx = result["idx"]
            
            # 检查idx是否增加（表示句子结束）
            is_final = idx > self.current_idx
            
            if is_final:
                logger.info(f"Final STT result (idx: {idx}): {text}")
                self.current_idx = idx
                self.accumulated_text = text
                
                # 调用回调函数，标记为最终结果
                if self.result_callback:
                    self.result_callback(text, True)
            else:
                logger.debug(f"Partial STT result: {text}")
                # 调用回调函数，标记为中间结果
                if self.result_callback:
                    self.result_callback(text, False)


class QuestionCollector:
    """问题收集器，用于收集完整的用户问题"""
    
    def __init__(self):
        self.question_callback = None
        self.async_question_callback = None
        self.current_question = ""
        
    def set_question_callback(self, callback: Callable[[str], None]):
        """设置问题完成回调函数（同步）"""
        self.question_callback = callback
        
    def set_async_question_callback(self, async_callback):
        """设置问题完成回调函数（异步）"""
        self.async_question_callback = async_callback
        
    def on_stt_result(self, text: str, is_final: bool):
        """处理STT结果"""
        if is_final and text.strip():
            self.current_question = text.strip()
            logger.info(f"Question collected: {self.current_question}")
            
            # 调用同步回调
            if self.question_callback:
                self.question_callback(self.current_question)
                
            # 调用异步回调
            if self.async_question_callback:
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self.async_question_callback(self.current_question))
                except RuntimeError:
                    # 如果没有运行的事件循环，忽略异步回调
                    pass
                
    def reset(self):
        """重置收集器"""
        self.current_question = ""
