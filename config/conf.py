import yaml
import dotenv
import os
from loguru import logger

dotenv.load_dotenv()

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logger.info(f"Project root directory: {PROJECT_ROOT}")

llm_config = {
    "api_key": os.getenv("LLM_AK", ""),
    "url": os.getenv("LLM_URL", "https://api.openai.com/v1"),
    "model": os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
}

stt_sr = int(os.getenv("TTS_SR", 24000))  # 默认值为24000Hz


openweather_api_key = os.getenv("OPENWEATHERMAP_API_KEY", "")


hass_config = {
    "enable": int(os.getenv("HASS_ENABLE", 0)),  # 1 to enable, 0 to disable
    "hass_url": os.getenv("HASS_URL", ""),
    "token": os.getenv("HASS_TOKEN")
}

logger.info(f"HASS configuration: {hass_config}")