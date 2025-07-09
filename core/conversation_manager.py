import asyncio
from typing import Optional, Callable
from loguru import logger
from pathlib import Path

from core.audio_manager import AudioManager
from core.keyword_detector import AsyncKeywordDetector
from core.async_speech_recognizer import AsyncSpeechRecognizer, QuestionCollector
from core.llm_streamer import ConversationLLM
from core.tts_streamer import TTSStreamer
from utils.audio_utils import play_notification_sound


class ConversationState:
    """对话状态枚举"""
    WAITING_KEYWORD = "waiting_keyword"
    LISTENING_QUESTION = "listening_question"
    PROCESSING_LLM = "processing_llm"
    PLAYING_RESPONSE = "playing_response"


class ConversationManager:
    """对话管理器 - 协调整个对话流程"""
    
    def __init__(self,
                 websocket_uri: str = "ws://localhost:8000/sttRealtime",
                 tts_url: str = "http://192.168.0.111:8001/tts",
                 notification_sound: str = "assets/media/click.mp3",
                 error_sound: str = "assets/media/error.mp3",
                 sample_rate: int = 16000,
                 **kwargs):
        
        # 创建统一音频管理器
        self.audio_manager = AudioManager(sample_rate=sample_rate)
        
        # 初始化各个组件
        self.keyword_detector = AsyncKeywordDetector(self.audio_manager, **kwargs)
        self.speech_recognizer = AsyncSpeechRecognizer(self.audio_manager, websocket_uri)
        self.question_collector = QuestionCollector()
        self.llm = ConversationLLM()
        self.tts_streamer = TTSStreamer(tts_url)
        
        # 音频文件路径
        self.notification_sound = notification_sound
        self.error_sound = error_sound
        
        # 状态管理
        self.state = ConversationState.WAITING_KEYWORD
        self.is_running = False
        self.current_tasks = []
        
        # 设置回调函数
        self._setup_callbacks()
        
        logger.info("Conversation manager initialized with unified audio manager")
        
    def _setup_callbacks(self):
        """设置各组件之间的回调函数"""
        # 关键词检测回调 - 使用异步回调
        self.keyword_detector.set_async_keyword_callback(self._on_keyword_detected)
        
        # 语音识别回调
        self.speech_recognizer.set_result_callback(self.question_collector.on_stt_result)
        
        # 问题收集回调 - 使用异步回调
        self.question_collector.set_async_question_callback(self._on_question_collected)
        
    async def start(self):
        """启动对话管理器"""
        if self.is_running:
            logger.warning("Conversation manager is already running")
            return
            
        self.is_running = True
        self.state = ConversationState.WAITING_KEYWORD
        
        logger.info("Starting conversation manager...")
        
        try:
            # 首先启动音频管理器
            if not self.audio_manager.start_stream():
                raise RuntimeError("Failed to start audio stream")
                
            # 启动关键词检测
            await self.keyword_detector.start_detection()
            
            # 主循环
            await self._main_loop()
            
        except Exception as e:
            logger.error(f"Conversation manager error: {e}")
        finally:
            await self.stop()
            
    async def stop(self):
        """停止对话管理器"""
        if not self.is_running:
            return
            
        self.is_running = False
        logger.info("Stopping conversation manager...")
        
        # 停止所有组件
        await self.keyword_detector.stop_detection()
        await self.speech_recognizer.stop_recognition()
        await self.tts_streamer.stop_playback()  # 确保停止音频播放
        
        # 停止音频管理器
        self.audio_manager.stop_stream()
        
        # 取消所有任务
        for task in self.current_tasks:
            if not task.done():
                task.cancel()
                
        await asyncio.gather(*self.current_tasks, return_exceptions=True)
        self.current_tasks.clear()
        
        logger.info("Conversation manager stopped")
        
    async def _main_loop(self):
        """主循环"""
        while self.is_running:
            await asyncio.sleep(0.1)
            
    async def _on_keyword_detected(self, keyword: str):
        """关键词检测回调（异步）"""
        logger.info(f"🎯 Keyword detected: {keyword}")
        
        if self.state != ConversationState.WAITING_KEYWORD:
            logger.info(f"Keyword detected but not in waiting state: {keyword} (current state: {self.state})")
            return
            
        logger.info(f"Processing keyword: {keyword}")
        
        try:
            # 立即切换状态，避免重复触发
            self.state = ConversationState.LISTENING_QUESTION
            self.question_collector.reset()
            
            # 并行启动提示音和语音识别，提升响应速度
            notification_task = asyncio.create_task(self._play_notification())
            recognition_task = asyncio.create_task(self._start_listening())
            
            # 等待两个任务完成
            await asyncio.gather(notification_task, recognition_task, return_exceptions=True)
            
            logger.info("Keyword processing completed, listening for user input")
            
        except Exception as e:
            logger.error(f"Error processing keyword: {e}")
            import traceback
            traceback.print_exc()
            self._reset_to_waiting()
        
    async def _play_notification(self):
        """播放提示音"""
        try:
            if Path(self.notification_sound).exists():
                # 异步播放提示音，不等待播放完成，加快响应速度
                loop = asyncio.get_running_loop()
                # 直接启动执行器任务，不等待完成
                loop.run_in_executor(
                    None, play_notification_sound, self.notification_sound
                )
                
                logger.info("Notification sound started playing")
                # 只等待很短时间确保音频开始播放
                await asyncio.sleep(0.1)
            else:
                logger.warning(f"Notification sound not found: {self.notification_sound}")
        except Exception as e:
            logger.error(f"Error playing notification sound: {e}")
            
    async def _start_listening(self):
        """开始监听用户语音"""
        # 注意：状态已在_on_keyword_detected中设置
        logger.info("🎤 Starting to listen for user question...")
        
        try:
            # 启动语音识别任务
            task = asyncio.create_task(self.speech_recognizer.start_recognition())
            self.current_tasks.append(task)
            
            logger.info("Speech recognition ready, waiting for user input...")
            
        except Exception as e:
            logger.error(f"Error starting speech recognition: {e}")
            import traceback
            traceback.print_exc()
            await self._play_error_sound()
            self._reset_to_waiting()
            
    async def _on_question_collected(self, question: str):
        """问题收集完成回调（异步）"""
        if self.state != ConversationState.LISTENING_QUESTION:
            return
            
        logger.info(f"Question collected: {question}")
        
        # 停止语音识别
        await self.speech_recognizer.stop_recognition()
        
        # 开始处理问题
        await self._process_question(question)
        
    async def _process_question(self, question: str):
        """处理用户问题"""
        self.state = ConversationState.PROCESSING_LLM
        
        logger.info("Processing question with LLM...")
        
        try:
            # 获取LLM回答
            text_queue = await self.llm.get_response(question)
            
            # 开始TTS播放
            self.state = ConversationState.PLAYING_RESPONSE
            logger.info("Starting TTS playback...")
            
            # 等待TTS播放完成 - 确保播放完成后才切换状态
            await self.tts_streamer.stream_play_from_queue(text_queue)
            
            logger.info("Response playback completed successfully")
            
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            import traceback
            traceback.print_exc()
            await self._play_error_sound()
        finally:
            # 确保在TTS完成后才重置状态
            logger.info("Question processing completed, returning to keyword waiting")
            self._reset_to_waiting()
            
    async def _play_error_sound(self):
        """播放错误提示音"""
        try:
            if Path(self.error_sound).exists():
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    None, play_notification_sound, self.error_sound
                )
        except Exception as e:
            logger.error(f"Error playing error sound: {e}")
            
    def _reset_to_waiting(self):
        """重置到等待关键词状态"""
        self.state = ConversationState.WAITING_KEYWORD
        logger.info("Reset to waiting for keyword...")
        
    def get_state(self) -> str:
        """获取当前状态"""
        return self.state
        
    def get_conversation_history(self):
        """获取对话历史"""
        return self.llm.get_history()
        
    def clear_conversation_history(self):
        """清空对话历史"""
        self.llm.clear_history()
        logger.info("Conversation history cleared")
