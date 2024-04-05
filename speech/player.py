# -*- coding: utf-8 -*-
import threading
from speech.tools import check_and_delete
import pyaudio
import threading
from pydub import AudioSegment
from pydub.utils import make_chunks
from time import sleep
from loguru import logger

class AudioPlayer:
    def __init__(self) -> None:
        self._bplaying = True
        self._playing = False
        self._audioGate = threading.Event()
        self._audioGate.set()
    def playSound( self, audioFilePath , delete=False):
        try:
            audioThread = threading.Thread( target=self._playSound, args=(audioFilePath, delete) )
            audioThread.start()
        except Exception as e:
            logger.error(f"播放音频失败：{str(e)}")
            return False

    def _playSound(self, audioFilePath, delete=False, volume=100.0):
        self._audioGate.wait()
        self._audioGate.clear()
        try:
            audio = pyaudio.PyAudio()
            if not audioFilePath:
                return True
            sound = AudioSegment.from_file(audioFilePath)
            self._audioGate.set()
            stream = audio.open(format = audio.get_format_from_width(sound.sample_width),
                channels = sound.channels,
                rate = sound.frame_rate,
                output = True)
            
            self._playing = True
            start = 0
            play_time = start
            length = sound.duration_seconds
            playchunk = sound[start*1000.0:(start+length)*1000.0] - (60 - (60 * (volume/100.0)))
            millisecondchunk = 50 / 1000.0
            self._bplaying = True
            for chunks in make_chunks(playchunk, millisecondchunk*1000):
                if not self._bplaying:
                    break
                play_time += millisecondchunk
                stream.write(chunks._data)
                if play_time >= start+length:
                    break
            stream.close()
            audio.terminate()
            self._playing = False
            if delete:
                check_and_delete(audioFilePath)
            logger.info(f"播放完成：{audioFilePath}")
            return True
        except Exception as e:
            logger.error(f"播放音频失败：{str(e)}")
            return False
    def stop(self):
        self._bplaying = False
        
    def is_playing(self):
        return self._playing


if __name__ == "__main__":
    audio_record = AudioPlayer()
    audio_record.playSound("piano2.wav")
    sleep(2)
    audio_record.stop()