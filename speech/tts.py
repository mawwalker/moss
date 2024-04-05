import os
import asyncio
import uuid
import edge_tts
from config.conf import config
from loguru import logger

class EdgeTTS():
    """
    edge-tts 引擎
    voice: 发音人，默认是 zh-CN-XiaoxiaoNeural
        全部发音人列表：命令行执行 edge-tts --list-voices 可以打印所有语音
    """

    def __init__(self, **args):
        self.voice = config['tts']['edge-tts']['voice_name']

    async def async_get_speech(self, phrase):
        try:
            os.makedirs(config['tmp_path'], exist_ok=True)
            tmpfile = os.path.join(config["tmp_path"], uuid.uuid4().hex + ".mp3")
            tts = edge_tts.Communicate(text=phrase, voice=self.voice)
            await tts.save(tmpfile)    
            logger.info(f"EdgeTTS Speech Synthesis Success! Path: {tmpfile}")
            return tmpfile
        except Exception as e:
            logger.error(f"EdgeTTS Speech Synthesis Failed: {str(e)}", exc_info=True)
            return None

    def get_speech(self, phrase):
        event_loop = asyncio.new_event_loop()
        tmpfile = event_loop.run_until_complete(self.async_get_speech(phrase))
        event_loop.close()
        return tmpfile