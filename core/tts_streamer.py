import asyncio
import requests
import tempfile
import os
from pathlib import Path
from typing import Optional
from loguru import logger
from utils.text_queue import TextQueue
from utils.audio_utils import StreamingAudioPlayer
from config.conf import stt_sr


class TTSStreamer:
    """TTS流式播放器"""
    
    def __init__(self, 
                 tts_url: str = "http://192.168.0.111:8001/tts",
                 character: str = "linzhiling"):
        self.tts_url = tts_url
        self.character = character
        self.audio_player = StreamingAudioPlayer(sample_rate=stt_sr)
        self.is_playing = False
        
    async def synthesize_text(self, text: str) -> Optional[bytes]:
        """合成单段文本为音频数据
        
        Args:
            text: 要合成的文本
            
        Returns:
            bytes: 音频数据，失败则返回None
        """
        try:
            logger.info(f"Synthesizing text: {text[:50]}...")
            
            # 调用TTS API
            data = {
                "text": text,
                "character": self.character,
            }
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: requests.post(self.tts_url, json=data, timeout=10)
            )
            
            if response.status_code != 200:
                logger.error(f"TTS request failed with status {response.status_code}")
                return None
                
            audio_data = response.content
            logger.debug(f"Received audio data: {len(audio_data)} bytes")
            return audio_data
            
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            return None
            
    async def stream_play_from_queue(self, text_queue: TextQueue):
        """从文本队列流式播放音频
        
        Args:
            text_queue: 文本队列对象
        """
        self.is_playing = True
        logger.debug("Starting TTS streaming playback...")
        
        # 启动音频播放
        await self.audio_player.start_playback()
        
        sentences_played = 0
        total_sentences = 0
        
        try:
            while self.is_playing:
                # 从队列获取句子
                sentence = await text_queue.get_sentence()
                
                if sentence is None:
                    # 检查是否已经结束
                    if text_queue.is_finished:
                        logger.debug(f"All sentences processed. Total: {total_sentences}")
                        self.is_playing = False
                        break
                    continue
                    
                if not sentence.strip():
                    continue
                
                total_sentences += 1
                logger.debug(f"Processing sentence {total_sentences} for TTS: {sentence}")
                
                # 合成音频
                audio_data = await self.synthesize_text(sentence)
                if audio_data:
                    # 添加到播放队列
                    await self.audio_player.add_audio_data(audio_data)
                    sentences_played += 1
                    logger.debug(f"Successfully queued sentence {sentences_played}: {sentence[:30]}...")
                else:
                    logger.warning(f"Failed to synthesize sentence {total_sentences}: {sentence}")
                    
            # 等待播放完成
            if sentences_played > 0:
                # 添加结束标记，告知音频播放器所有数据已添加完毕
                await self.audio_player.add_audio_data(b'')  # 空数据作为结束标记
                logger.debug("Waiting for audio playback to complete...")
                await self.audio_player.wait_until_finished()
            else:
                logger.info("No sentences were successfully processed for TTS")
                    
        except Exception as e:
            logger.error(f"TTS streaming error: {e}")
        finally:
            self.is_playing = False
            logger.info(f"TTS streaming completed. Played {sentences_played}/{total_sentences} sentences")
            
    async def stop_playback(self):
        """停止播放"""
        logger.info("Stopping TTS playback...")
        self.is_playing = False
        await self.audio_player.stop_playback()
        
    async def play_single_text(self, text: str) -> bool:
        """播放单段文本
        
        Args:
            text: 要播放的文本
            
        Returns:
            bool: 是否成功播放
        """
        audio_data = await self.synthesize_text(text)
        if audio_data:
            await self.audio_player.start_playback()
            await self.audio_player.add_audio_data(audio_data)
            await self.audio_player.wait_until_finished()
            return True
        return False


class BatchTTSPlayer:
    """批量TTS播放器"""
    
    def __init__(self, tts_streamer: TTSStreamer):
        self.tts_streamer = tts_streamer
        
    async def play_text_list(self, texts: list, delay: float = 0.5):
        """播放文本列表
        
        Args:
            texts: 文本列表
            delay: 每段文本之间的延迟（秒）
        """
        logger.info(f"Playing {len(texts)} text segments...")
        
        for i, text in enumerate(texts):
            if not text.strip():
                continue
                
            logger.info(f"Playing segment {i+1}/{len(texts)}: {text[:50]}...")
            
            success = await self.tts_streamer.play_single_text(text)
            if not success:
                logger.warning(f"Failed to play segment {i+1}")
                
            # 添加延迟
            if i < len(texts) - 1 and delay > 0:
                await asyncio.sleep(delay)
                
        logger.info("Batch TTS playback completed")
