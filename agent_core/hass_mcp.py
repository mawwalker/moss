from langchain_core.tools import StructuredTool
from pydantic import BaseModel
from langchain_mcp_tools import convert_mcp_to_langchain_tools
from loguru import logger
import os
from config.conf import openweather_api_key, hass_config, PROJECT_ROOT

async def build_hass_tools() -> tuple:
    try:
        hass_mcp_config = {
            "homeassistant": {
                "transport": "stdio",
                "command": "uv",
                "args": [
                    "run",
                    "mcp",
                    "run",
                    "hass-mcp/app/server.py",
                ],
                "env": {
                    "HA_URL": hass_config["hass_url"],
                    "HA_TOKEN": hass_config["token"],  # Uncomment if token is needed
                    "PYTHONPATH": os.path.join(PROJECT_ROOT, "hass-mcp"),
                }
            }
            
        }
        tools, cleanup = await convert_mcp_to_langchain_tools(
            hass_mcp_config,
        )
        return tools, cleanup
    except Exception as e:
        logger.error(f"Failed to build HASS tools: {e}")
        # Return empty tools and a no-op cleanup function
        return [], lambda: None