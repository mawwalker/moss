#!/usr/bin/env python3
"""
实时语音对话程序
支持关键词唤醒、语音识别、LLM对话和TTS语音合成的完整流程
"""

import asyncio
import argparse
import signal
from pathlib import Path
from loguru import logger
from core.conversation_manager import ConversationManager


class RealTimeVoiceChat:
    """实时语音对话主程序"""
    
    def __init__(self, args):
        self.args = args
        self.conversation_manager = None
        self.is_running = False
        
    async def setup(self):
        """初始化程序"""
        logger.info("Setting up Real-Time Voice Chat...")
        
        # 验证必要的文件和目录
        self._validate_assets()
        
        # 初始化对话管理器
        self.conversation_manager = ConversationManager(
            websocket_uri=self.args.stt_uri,
            tts_url=self.args.tts_url,
            notification_sound=self.args.notification_sound,
            error_sound=self.args.error_sound,
            sample_rate=self.args.sample_rate,
            # 关键词检测参数
            tokens_path=self.args.tokens,
            encoder_path=self.args.encoder,
            decoder_path=self.args.decoder,
            joiner_path=self.args.joiner,
            keywords_file=self.args.keywords_file,
            keywords_score=self.args.keywords_score,
            keywords_threshold=self.args.keywords_threshold
        )
        
        logger.info("Setup completed")
        
    def _validate_assets(self):
        """验证必要的资源文件"""
        required_files = [
            self.args.tokens,
            self.args.encoder, 
            self.args.decoder,
            self.args.joiner,
            self.args.keywords_file
        ]
        
        for file_path in required_files:
            if not Path(file_path).exists():
                raise FileNotFoundError(f"Required file not found: {file_path}")
                
        logger.info("All required asset files validated")
        
    async def run(self):
        """运行主程序"""
        logger.info("Starting Real-Time Voice Chat...")
        logger.info("说明：程序将持续监听关键词，检测到关键词后会播放提示音并开始语音识别")
        logger.info("按 Ctrl+C 退出程序")
        
        self.is_running = True
        
        try:
            # 设置信号处理器
            self._setup_signal_handlers()
            
            # 启动对话管理器
            await self.conversation_manager.start()
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            await self.cleanup()
            
    def _setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            self.is_running = False
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    async def cleanup(self):
        """清理资源"""
        logger.info("Cleaning up...")
        
        self.is_running = False
        
        if self.conversation_manager:
            await self.conversation_manager.stop()
            
        logger.info("Cleanup completed")


def get_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="实时语音对话程序",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # 关键词检测参数
    parser.add_argument(
        "--tokens",
        type=str,
        default="assets/sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01/tokens.txt",
        help="tokens.txt文件路径"
    )
    
    parser.add_argument(
        "--encoder",
        type=str,
        default="assets/sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01/encoder-epoch-99-avg-1-chunk-16-left-64.onnx",
        help="编码器模型路径"
    )
    
    parser.add_argument(
        "--decoder",
        type=str,
        default="assets/sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01/decoder-epoch-99-avg-1-chunk-16-left-64.onnx",
        help="解码器模型路径"
    )
    
    parser.add_argument(
        "--joiner",
        type=str,
        default="assets/sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01/joiner-epoch-99-avg-1-chunk-16-left-64.onnx",
        help="连接器模型路径"
    )
    
    parser.add_argument(
        "--keywords-file",
        type=str,
        default="assets/keywords_zh.txt",
        help="关键词文件路径"
    )
    
    parser.add_argument(
        "--keywords-score",
        type=float,
        default=2.0,
        help="关键词提升分数"
    )
    
    parser.add_argument(
        "--keywords-threshold",
        type=float,
        default=0.15,
        help="关键词触发阈值"
    )
    
    # 语音识别参数
    parser.add_argument(
        "--stt-uri",
        type=str,
        default="ws://192.168.0.111:8000/sttRealtime",
        help="STT WebSocket服务地址"
    )
    
    # TTS参数
    parser.add_argument(
        "--tts-url",
        type=str,
        default="http://192.168.0.111:8001/tts",
        help="TTS服务地址"
    )
    
    # 音频参数
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        help="音频采样率"
    )
    
    # 提示音文件
    parser.add_argument(
        "--notification-sound",
        type=str,
        default="assets/media/click.mp3",
        help="提示音文件路径"
    )
    
    parser.add_argument(
        "--error-sound",
        type=str,
        default="assets/media/error.mp3",
        help="错误提示音文件路径"
    )
    
    # 调试选项
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="启用详细日志输出"
    )
    
    return parser.parse_args()


def setup_logging(verbose: bool = False):
    """设置日志"""
    log_level = "DEBUG" if verbose else "INFO"
    
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True
    )


async def main():
    """主函数"""
    args = get_args()
    setup_logging(args.verbose)
    
    # 创建并运行程序
    app = RealTimeVoiceChat(args)
    
    try:
        await app.setup()
        await app.run()
    except Exception as e:
        logger.error(f"Application error: {e}")
        return 1
        
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
        exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        exit(1)
