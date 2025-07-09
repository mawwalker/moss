import yaml
import dotenv
import os

dotenv.load_dotenv()

with open("config/config.yml", 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

ADDITION_SYSTEM_MESSAGE = """You Are A helpful Home Assistant. You can control the devices and answer any other questions. I'm in '{location}' now. In my House, the devices are as blow (dict format, where the value is use purpose, the key is the entity_id):
        {device_list}. You can control the devices by using the given tools. You must use the correct parameters when using the tools. Sometimes before you change the value of some device, 
        you should first query the current state of the device to confirm how to change the value. ALWAYS outputs the final result to {language}."""

llm_config = {
    "api_key": os.getenv("LLM_AK", ""),
    "url": os.getenv("LLM_URL", "https://api.openai.com/v1"),
    "model": os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
}

stt_sr = int(os.getenv("TTS_SR", 24000))  # 默认值为24000Hz


openweather_api_key = os.getenv("OPENWEATHERMAP_API_KEY", "")