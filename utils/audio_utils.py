import asyncio
import numpy as np
import sounddevice as sd
import io
import pygame
import wave
from typing import Optional
from loguru import logger
from pathlib import Path


class StreamingAudioPlayer:
    """流式音频播放器 - 支持音频队列和中断"""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.audio_queue = asyncio.Queue()
        self.is_playing = False
        self.should_stop = False
        self.current_stream = None
        self.play_task = None
        
    async def add_audio_data(self, audio_data: bytes):
        """添加音频数据到播放队列"""
        if not self.should_stop:
            try:
                if len(audio_data) == 0:
                    # 空数据作为结束标记
                    await self.audio_queue.put(None)
                    logger.debug("Added end marker to audio queue")
                else:
                    # 将音频字节转换为numpy数组
                    audio_array = self._bytes_to_audio_array(audio_data)
                    if len(audio_array) > 0:
                        await self.audio_queue.put(audio_array)
                        logger.debug(f"Added audio data to queue, size: {len(audio_data)} bytes")
            except Exception as e:
                logger.error(f"Error adding audio data: {e}")
    
    def _bytes_to_audio_array(self, audio_data: bytes) -> np.ndarray:
        """将音频字节数据转换为numpy数组"""
        try:
            # 尝试解析WAV格式
            with io.BytesIO(audio_data) as audio_io:
                with wave.open(audio_io, 'rb') as wav_file:
                    frames = wav_file.readframes(wav_file.getnframes())
                    sample_width = wav_file.getsampwidth()
                    
                    if sample_width == 2:  # 16-bit
                        audio_array = np.frombuffer(frames, dtype=np.int16)
                        # 转换为float32, 范围[-1, 1]
                        # audio_array = audio_array.astype(np.float32) / 32768.0
                    else:
                        raise ValueError(f"Unsupported sample width: {sample_width}")
                        
                    return audio_array
        except Exception as e:
            logger.error(f"Error parsing audio data: {e}")
            return np.array([], dtype=np.float32)
    
    async def start_playback(self):
        """开始播放"""
        if self.is_playing:
            return
            
        self.is_playing = True
        self.should_stop = False
        self.play_task = asyncio.create_task(self._playback_loop())
        logger.debug("Started streaming audio playback")
    
    def play_audio_file(self, file_path: str) -> bool:
        """播放音频文件"""
        try:
            pygame.mixer.init()
            self.is_playing = True
            
            logger.debug(f"Playing audio: {file_path}")
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # 等待播放完成
            while pygame.mixer.music.get_busy() and self.is_playing:
                pygame.time.wait(100)
                
            return True
            
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
            return False
        finally:
            try:
                pygame.mixer.quit()
            except:
                pass
            self.is_playing = False
    
    async def stop_playback(self):
        """停止播放并清空队列"""
        logger.info("Stopping audio playback...")
        self.should_stop = True
        self.is_playing = False
        
        # 清空队列
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        # 停止当前播放
        if self.current_stream:
            self.current_stream.stop()
            
        # 等待播放任务结束
        if self.play_task:
            self.play_task.cancel()
            try:
                await self.play_task
            except asyncio.CancelledError:
                pass
            self.play_task = None
            
        logger.info("Audio playback stopped")
    
    async def _playback_loop(self):
        """播放循环"""
        try:
            while self.is_playing and not self.should_stop:
                try:
                    # 获取音频数据，超时时间短一些以便及时响应停止信号
                    audio_data = await asyncio.wait_for(
                        self.audio_queue.get(), timeout=0.5
                    )
                    
                    if self.should_stop:
                        break
                    
                    # 检查结束标记
                    if audio_data is None:
                        logger.debug("Received end marker, stopping playback loop")
                        break
                        
                    # 播放音频数据
                    await self._play_audio_array(audio_data)
                    
                except asyncio.TimeoutError:
                    # 超时继续循环，检查是否需要停止
                    # 如果队列为空且没有停止信号，继续等待
                    continue
                except Exception as e:
                    logger.error(f"Error in playback loop: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Playback loop error: {e}")
        finally:
            self.is_playing = False
            logger.debug("Playback loop ended")
    
    async def _play_audio_array(self, audio_data: np.ndarray):
        """播放音频数组"""
        if len(audio_data) == 0 or self.should_stop:
            return
            
        try:
            # 使用sounddevice播放
            await asyncio.get_event_loop().run_in_executor(
                None, self._sync_play_audio, audio_data
            )
        except Exception as e:
            logger.error(f"Error playing audio array: {e}")
    
    def _sync_play_audio(self, audio_data: np.ndarray):
        """同步播放音频"""
        try:
            # sd.play(audio_data, samplerate=self.sample_rate, blocking=True)
            # sd.wait()  # 等待播放完成
            pygame.mixer.init(frequency=self.sample_rate, size=-16, channels=1)
            sound = pygame.sndarray.make_sound(audio_data)
            sound.play()
            pygame.time.wait(int(sound.get_length() * 1000))
            pygame.quit()
        except Exception as e:
            logger.error(f"Error in sync audio play: {e}")
    
    def is_queue_empty(self) -> bool:
        """检查队列是否为空"""
        return self.audio_queue.empty()
    
    async def wait_until_finished(self):
        """等待播放完成"""
        while self.is_playing and not self.should_stop:
            # 检查队列是否为空且播放任务是否还在运行
            if self.audio_queue.empty() and (not self.play_task or self.play_task.done()):
                break
            await asyncio.sleep(0.1)
        
        # 确保播放任务完成
        if self.play_task and not self.play_task.done():
            try:
                await asyncio.wait_for(self.play_task, timeout=2.0)
            except asyncio.TimeoutError:
                logger.warning("Play task timeout, forcing stop")
                self.play_task.cancel()
            except Exception as e:
                logger.error(f"Error waiting for play task: {e}")
        
        logger.debug("Audio playback finished")


class AudioRecorder:
    """音频录制器"""
    
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device_id = None
        self.is_recording = False
        
    def find_best_device(self) -> Optional[int]:
        """查找最佳音频输入设备"""
        devices = sd.query_devices()
        input_devices = [i for i, dev in enumerate(devices) if dev['max_input_channels'] > 0]
        
        if not input_devices:
            logger.error("No input devices found!")
            return None
            
        logger.debug("Available input devices:")
        for i in input_devices:
            dev = devices[i]
            logger.debug(f"  {i}: {dev['name']} (channels: {dev['max_input_channels']}, rate: {dev['default_samplerate']})")
        
        # 尝试找到支持目标采样率的设备
        for device_id in input_devices:
            try:
                sd.check_input_settings(
                    device=device_id, 
                    channels=self.channels, 
                    dtype='float32', 
                    samplerate=self.sample_rate
                )
                logger.debug(f"Selected device {device_id}: {devices[device_id]['name']}")
                return device_id
            except:
                continue
                
        # 如果没有找到，使用第一个可用设备
        device_id = input_devices[0]
        logger.warning(f"Using fallback device {device_id}: {devices[device_id]['name']}")
        return device_id
        
    def setup(self) -> bool:
        """设置录音设备"""
        self.device_id = self.find_best_device()
        return self.device_id is not None


def play_notification_sound(sound_file: str) -> bool:
    """播放提示音"""
    if not Path(sound_file).exists():
        logger.warning(f"Notification sound file not found: {sound_file}")
        return False
        
    player = StreamingAudioPlayer()
    return player.play_audio_file(sound_file)


def audio_array_to_bytes(audio_data: np.ndarray) -> bytes:
    """将音频数组转换为字节"""
    if audio_data.dtype != np.float32:
        audio_data = audio_data.astype(np.float32)
    
    # 转换为int16格式
    audio_int16 = (audio_data * 32767).astype(np.int16)
    return audio_int16.tobytes()


def normalize_audio(audio_data: np.ndarray) -> np.ndarray:
    """归一化音频数据"""
    if len(audio_data) == 0:
        return audio_data
        
    max_val = np.max(np.abs(audio_data))
    if max_val > 0:
        return audio_data / max_val
    return audio_data
