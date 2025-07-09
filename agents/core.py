from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import StructuredTool
from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt.chat_agent_executor import AgentState
from langgraph.config import get_stream_writer
from langchain_core.messages.ai import AIMessage
from typing import Any, AsyncGenerator
from agents.prompts import agent_additional_prompts
from config.conf import llm_config
from loguru import logger
from agents.tools import init_tools


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
        self.agent = create_react_agent(
            model=self.llm,
            tools=init_tools(),
            prompt=self.dynamic_system_prompt
        )
        
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
        logger.debug(f"config: {config}")
        result = self.agent.stream(
            {"messages": messages},
            stream_mode=["updates", "messages", "custom"],
            config=config,
        )

        for stream_mode, chunk in result:
            if stream_mode == "messages":
                # import ipdb; ipdb.set_trace()
                content = chunk[0].content
                if content and isinstance(chunk[0], AIMessage):
                    logger.debug(f"{content}")
                    yield content
        logger.info("MossAgent run completed.")
                
if __name__ == "__main__":
    # 测试MossAgent
    agent = MossAgent()
    messages = [
        {"role": "user", "content": "你好，今天杭州的天气怎么样？"},
        # {"role": "assistant", "content": "你好！我可以帮你查询天气。"}
    ]
    
    # 运行代理
    import asyncio
    asyncio.run(agent.run(messages, config=RunnableConfig(configurable={"current_date": "2023-10-01"})))