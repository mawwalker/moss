from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import StructuredTool
from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.config import get_stream_writer
from langchain_core.messages.ai import AIMessage
import asyncio
from typing import Any, AsyncGenerator
from agent_core.prompts import agent_additional_prompts
from config.conf import llm_config
from loguru import logger
import datetime
from agent_core.tools import init_tools


class MossAgent:
    """Moss智能管家"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=llm_config["model"],
            temperature=0.1,
            api_key=llm_config["api_key"],
            base_url=llm_config["url"],
            # extra_body={"enable_thinking": False}
        )
        self.agent = None
        self._initialized = False
        self._cleanup_funcs = []  # Store cleanup functions
        
    async def _initialize(self):
        """异步初始化agent"""
        if not self._initialized:
            tools, cleanup_funcs = await init_tools()
            self._cleanup_funcs.extend(cleanup_funcs)
            self.agent = create_react_agent(
                model=self.llm,
                tools=tools,
                prompt=self.dynamic_system_prompt
            )
            self._initialized = True
    
    async def cleanup(self):
        """Clean up resources"""
        for cleanup_func in self._cleanup_funcs:
            try:
                if asyncio.iscoroutinefunction(cleanup_func):
                    await cleanup_func()
                else:
                    cleanup_func()
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
        self._cleanup_funcs.clear()

    async def __aenter__(self):
        await self._initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
        
    @staticmethod
    def dynamic_system_prompt(state: AgentState, config: RunnableConfig) -> list[AnyMessage]:
        current_date = config.get("configurable", {}).get("current_date", "")
        logger.debug(f"Dynamic system prompt with current date: {current_date}")
        system_msg = agent_additional_prompts.format(
            current_date=current_date,
        )
        return [{"role": "system", "content": system_msg}] + state["messages"]

    async def run(self, messages: list[AnyMessage], config: RunnableConfig = None) -> AsyncGenerator[Any, Any]:
        """运行Moss智能管家"""
        await self._initialize()  # 确保agent已初始化
        
        logger.debug(f"config: {config}")
        result = self.agent.astream(
            {"messages": messages},
            stream_mode=["updates", "messages", "custom"],
            config=config,
        )

        async for stream_mode, chunk in result:
            print(chunk)
            if stream_mode == "messages":
                # import ipdb; ipdb.set_trace()
                content = chunk[0].content
                if content and isinstance(chunk[0], AIMessage):
                    logger.debug(f"{content}")
                    yield content
        logger.info("MossAgent run completed.")


if __name__ == "__main__":
    import asyncio
    
    messages = [
        # {"role": "user", "content": "你好，今天杭州的天气怎么样？"},
        # {"role": "user", "content": "打开youtube搜搜最近的热门"},
        # {"role": "user", "content": "google 搜一下btc最新价格"},
        # {"role": "user", "content": "google 搜一下btc最新价格"},
        # {"role": "user", "content": "我现在设备的状态是什么样的"},
        {"role": "user", "content": "关闭床头灯"},
        # {"role": "user", "content": "打开床头灯"},
        # {"role": "user", "content": "添加买东西到待办中"},
        # {"role": "assistant", "content": "你好！我可以帮你查询天气。"}
    ]
    
    async def main():
        async with MossAgent() as agent:
            async for chunk in agent.run(messages, config=RunnableConfig(configurable={"current_date": "2025-07-10"})):
                print(chunk)
    
    asyncio.run(main())
