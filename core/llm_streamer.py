import asyncio
from openai import AsyncOpenAI
from typing import Callable, List, Dict, Any
from loguru import logger
from config.conf import llm_config, language
from utils.text_queue import TextQueue
from langchain_core.runnables import RunnableConfig
from datetime import datetime
from agent_core.core import MossAgent


class LLMStreamer:
    """LLM流式生成器"""
    
    def __init__(self, config: dict = None):
        self.config = config or llm_config
        self.client = AsyncOpenAI(
            api_key=self.config["api_key"],
            base_url=self.config["url"]
        )
        self.text_queue = TextQueue()
        self.agent = MossAgent()
        
    async def stream_chat(self, 
                         messages: List[Dict[str, str]], 
                         temperature: float = 0.1,
                         extra_body: Dict[str, Any] = None) -> TextQueue:
        """流式聊天生成
        
        Args:
            messages: 对话消息列表
            temperature: 生成温度
            extra_body: 额外参数
            
        Returns:
            TextQueue: 文本队列对象
        """
        self.text_queue.reset()
        
        try:
            logger.debug("Starting LLM streaming...")
            configurable = {
                "current_date": datetime.now().strftime("%Y-%m-%d"),
                "language": language
            }
            stream = self.agent.run(messages, config=RunnableConfig(configurable=configurable))
            async for chunk in stream:
                await self.text_queue.put_chunk(chunk)
                
                    
            # 标记生成结束
            await self.text_queue.put_final()
            logger.info("LLM streaming completed")
            
        except Exception as e:
            logger.error(f"LLM streaming error: {e}")
            await self.text_queue.put_final()
            
        return self.text_queue
        
    async def generate_response(self, question: str) -> TextQueue:
        """生成对用户问题的回答
        
        Args:
            question: 用户问题
            
        Returns:
            TextQueue: 文本队列对象
        """
        messages = [
            {
                "role": "user", 
                "content": question
            }
        ]
        
        logger.info(f"Generating response for question: {question}")
        return await self.stream_chat(messages)


class ConversationLLM:
    """对话式LLM管理器，支持多轮对话"""
    
    def __init__(self, config: dict = None, system_prompt: str = None):
        self.streamer = LLMStreamer(config)
        self.conversation_history = []
            
    def add_user_message(self, message: str):
        """添加用户消息"""
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        
    def add_assistant_message(self, message: str):
        """添加助手消息"""
        self.conversation_history.append({
            "role": "assistant", 
            "content": message
        })
        
    async def get_response(self, user_question: str) -> TextQueue:
        """获取对用户问题的回答
        
        Args:
            user_question: 用户问题
            
        Returns:
            TextQueue: 文本队列对象
        """
        
        # 添加用户消息
        self.add_user_message(user_question)
        
        # 生成回答
        text_queue = await self.streamer.stream_chat(self.conversation_history)
        
        # 收集完整回答以添加到历史记录
        asyncio.create_task(self._collect_response(text_queue))
        
        return text_queue
        
    async def _collect_response(self, text_queue: TextQueue):
        """收集完整的回答并添加到历史记录"""
        # 等待流式生成完成
        while not text_queue.is_finished:
            await asyncio.sleep(0.1)
        
        # 从TextQueue获取完整的生成文本
        full_response = text_queue.get_full_text()
                
        if full_response.strip():
            self.add_assistant_message(full_response.strip())
            logger.debug(f"Added assistant response to history: {full_response[:100]}...")
            
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history = []
        
    def get_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.conversation_history.copy()
