# -*- coding:utf-8 -*-
import os
from loguru import logger
os.environ["OPENAI_API_VERSION"] = "2023-05-15"
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent, create_structured_chat_agent
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import tool, Tool, initialize_agent, load_tools
from config.conf import config, ADDITION_SYSTEM_MESSAGE
from .tools import brightness_control_tool, feeder_out_tool, get_attr_tool, hvac_control_tool, openweathermap_api


hass_url = config['agent_config']['hass']['host']
hass_port = config['agent_config']['hass']['port']
hass_headers = {'Authorization': config['agent_config']['hass']['key'], 'content-type': 'application/json'}


class Agents(object):
    
    def __init__(self):
        self.langchain_init()
        
    def langchain_init(self):
        self.llm = None
        llm_provider = config['llm']['provider']
        if llm_provider == 'azure':
            api_key = config['llm']['azure']['api_key']
            endpoint = config['llm']['azure']['endpoint']
            deployment = config['llm']['azure']['deployment']
            self.llm = AzureChatOpenAI(azure_deployment=deployment, api_key=api_key, azure_endpoint=endpoint)
        structured_chat_prompt = hub.pull("hwchase17/structured-chat-agent")
        structured_chat_system = structured_chat_prompt.messages[0].prompt.template
        structured_chat_human = structured_chat_prompt.messages[2].prompt.template
        prompt = ChatPromptTemplate.from_messages([
            ('system', structured_chat_system+ ADDITION_SYSTEM_MESSAGE),
            structured_chat_human
            ]
        )
        
        internal_tools = load_tools(["google-search"], self.llm)
        
        
        tools = [brightness_control_tool, feeder_out_tool, get_attr_tool, hvac_control_tool, openweathermap_api
                 ] + internal_tools
        agent = create_structured_chat_agent(self.llm, tools, prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=3, handle_parsing_errors=True)
        self.device_dict = config['agent_config']['hass']['entity_ids']

    def handle(self, text):
        handle_result = self.agent_executor.invoke({"input": f"{text}", "device_list": self.device_dict,
                                                    "location": config['location'], 
                                                    "language": f"{config['agent_config']['language']}"})
        output_text = handle_result["output"]
        return output_text
 
if __name__ == "__main__":
    agent = Agents()
    text = "杭州天气怎么样"
    response = agent.handle(text)