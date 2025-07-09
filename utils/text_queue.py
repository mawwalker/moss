import asyncio
import re
from typing import Optional
import nltk
from nltk.tokenize import sent_tokenize
from loguru import logger


class TextQueue:
    """文本队列管理器，用于处理流式文本生成和消费"""
    
    def __init__(self):
        self.queue = asyncio.Queue()
        self.current_sentence = ""
        self.is_finished = False
        self.full_text = ""  # 保存完整的生成文本
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('tokenizers/punkt_tab')
        except LookupError:
            nltk.download('punkt_tab')
            nltk.download('punkt')
        
    async def put_chunk(self, text_chunk: str):
        """添加文本块到队列"""
        if text_chunk:
            self.current_sentence += text_chunk
            self.full_text += text_chunk  # 累积完整文本
            logger.debug(f"Added chunk: {text_chunk}")
            
            # 检查是否形成完整句子
            sentences = self._extract_sentences(self.current_sentence)
            for sentence in sentences:
                if sentence.strip():
                    await self.queue.put(sentence.strip())
                    logger.info(f"Complete sentence queued: {sentence.strip()}")
            
    async def put_final(self):
        """标记流式生成结束，处理剩余文本"""
        if self.current_sentence.strip():
            await self.queue.put(self.current_sentence.strip())
            logger.info(f"Final sentence queued: {self.current_sentence.strip()}")
        
        self.is_finished = True
        await self.queue.put(None)  # 结束标记
        
    async def get_sentence(self) -> Optional[str]:
        """获取一个完整的句子"""
        try:
            sentence = await asyncio.wait_for(self.queue.get(), timeout=1.0)
            return sentence
        except asyncio.TimeoutError:
            return None
            
    def _extract_sentences(self, text: str) -> list:
        """使用NLTK进行句子分割"""
        # NLTK对中英文混合文本的处理
        sentences = sent_tokenize(text, language='english')
        
        complete_sentences = []
        total_length = 0
        
        for sentence in sentences[:-1]:  # 除了最后一句
            complete_sentences.append(sentence.strip())
            total_length += len(sentence)
        
        # 最后一句可能不完整
        if sentences:
            remaining_start = sum(len(s) for s in sentences[:-1])
            self.current_sentence = text[remaining_start:].strip()
        else:
            self.current_sentence = text
            
        return complete_sentences
        
    def reset(self):
        """重置队列"""
        self.queue = asyncio.Queue()
        self.current_sentence = ""
        self.is_finished = False
        self.full_text = ""  # 重置完整文本
        
    def get_full_text(self) -> str:
        """获取完整的生成文本"""
        return self.full_text
