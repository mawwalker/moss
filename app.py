# import os
from loguru import logger
import signal 
import time
from speech.player import AudioPlayer
import azure.cognitiveservices.speech as speechsdk
from agents import Agents
from speech.tts import EdgeTTS
from config.conf import config

Sentry = True
def SignalHandler_SIGINT(SignalNumber,Frame):
   global Sentry 
   Sentry = False
   
signal.signal(signal.SIGINT,SignalHandler_SIGINT)

class Moss:
    def __init__(self) -> None:
        self.subscription_key = config['asr']['azure']['speech_key']
        self.region = config['asr']['azure']['speech_region']
        self.model_path = config['keyword']['azure']['model']
        self.speech_config = speechsdk.SpeechConfig(subscription=self.subscription_key, region=self.region)
        self.speech_config.speech_recognition_language = config['asr']['azure']['language']
        self.keyword_recognizer = speechsdk.KeywordRecognizer()
        self.keyword_model = speechsdk.KeywordRecognitionModel(self.model_path)
        self.speech_recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config)
        self.player = AudioPlayer()
        self.agent = Agents()
        self.tts = EdgeTTS()
        self.ttrigger_file = "assets/media/click.mp3"
        self.error_file = "assets/media/error.mp3"
        self.pass_file = "assets/media/pass.mp3"

    def handle(self, text):
        """Handle recognized speech and respond using text-to-speech"""
        logger.info(f"[AZURE SPEECH RECOGNITION]: Recognized speech: {text}")
        try:
            response = self.agent.handle(text)
            logger.info(f"[Agent Response]: Received response: {response}")
            logger.info("[TTS]: Starting Text To Speech")
            tmpfile = self.tts.get_speech(response)
            self.play(tmpfile, delete=True)
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
            logger.info(f"[TTS]: Error occurred while processing text: {text}")
            self.play(self.error_file)
            
    
    def listen_speech(self):
        """Listen for speech input"""
        logger.info("[AZURE SPEECH RECOGNITION]: Listening for input")
        try:
            result = self.speech_recognizer.recognize_once_async().get()
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                self.play(self.pass_file)
                logger.info(f"[AZURE SPEECH RECOGNITION]: Recognized speech: {result.text}")
                return result.text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                nomatch_detail = result.no_match_details
                logger.info(f"[AZURE SPEECH RECOGNITION]: No match found: {nomatch_detail}")
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                logger.info(f"[AZURE SPEECH RECOGNITION]: Cancellation reason: {cancellation_details.reason}")
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    logger.info(f"[AZURE SPEECH RECOGNITION]: Error details: {cancellation_details.error_details}")
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
        return ""
    
    def listen_keyword(self):
        """Listen for a specific keyword to activate speech recognition"""
        logger.info("[AZURE SPEECH RECOGNITION]: Listening for wakeup keyword")
        try:
            result = self.keyword_recognizer.recognize_once_async(model=self.keyword_model).get()
            if not result:
                return False
            if result.reason == speechsdk.ResultReason.RecognizedKeyword:
                logger.info("[AZURE SPEECH RECOGNITION]: Wakeup word detected")
                return True
            elif result.reason == speechsdk.ResultReason.NoMatch:
                nomatch_detail = result.no_match_details
                logger.info(f"[AZURE SPEECH RECOGNITION]: No match found: {nomatch_detail}")
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                logger.info(f"[AZURE SPEECH RECOGNITION]: Cancellation reason: {cancellation_details.reason}")
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    logger.info(f"[AZURE SPEECH RECOGNITION]: Error details: {cancellation_details.error_details}")
        except Exception as e:
            logger.error(f"An error occurred: {e}", exc_info=True)
        return False
    
    def interrupt(self):
        if self.player and self.player.is_playing():
            self.player.stop()
            
    def play(self, src, delete=False):
        """播放一个音频"""
        if self.player:
            self.interrupt()
        self.player.playSound(src, delete)

    def loop(self):
        global Sentry
        while Sentry:
            try:
                keyword_result = self.listen_keyword()
                if keyword_result:
                    self.play(self.ttrigger_file)
                    speech_result = self.listen_speech()
                    if speech_result:
                        self.handle(speech_result)
            except Exception as e:
                logger.error(f"An error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    moss = Moss()
    moss.loop()