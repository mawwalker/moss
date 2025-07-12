from langchain_core.tools import StructuredTool
from pydantic import BaseModel
from langchain_community.utilities import OpenWeatherMapAPIWrapper
from langchain_tavily import TavilySearch
from langchain_mcp_tools import convert_mcp_to_langchain_tools
from agent_core.hass_mcp import build_hass_tools
from loguru import logger
from config.conf import openweather_api_key, hass_config


class OpenWeatherMapInput(BaseModel):
    location_code: str
    
class DuckDuckGoSearchInput(BaseModel):
    query: str
    

def openweathermap(location_code):
    logger.info(f"Fetching weather data for location: {location_code}")
    weather = OpenWeatherMapAPIWrapper(openweathermap_api_key=openweather_api_key)
    weather_data = weather.run(location_code)
    logger.info(f"Weather data fetched: {weather_data}")
    return weather_data

openweathermap_tool = StructuredTool.from_function(
    func=openweathermap,
    name="open_weather_map",
    description="""This tool fetches weather data from OpenWeatherMap API. Input is a location code In English ONLY. For example, "London", "London,UK" or "London,GB" for London, United Kingdom.
    You must check the location code before using this tool. The location code must be in English
    """,
    args_schema=OpenWeatherMapInput
)

tavily_search_tool = TavilySearch(
    max_result=5,
    topic="general",
)


async def init_tools():
    """Initialize and return a list of tools for the agent."""
    tools = [
        openweathermap_tool,
        tavily_search_tool,
        # Add other tools here as needed
    ]
    
    cleanup_funcs = []
    
    if hass_config["enable"]:
        logger.debug("Initializing HASS tools...")
        try:
            hass_tools, cleanup = await build_hass_tools()
            tools.extend(hass_tools)
            cleanup_funcs.append(cleanup)
        except Exception as e:
            logger.error(f"Failed to initialize HASS tools: {e}")
            # Continue without HASS tools
    
    logger.info(f"Initialized tools: {[tool.name for tool in tools]}")
    return tools, cleanup_funcs


if __name__ == "__main__":
    # Test the OpenWeatherMap tool
    location = "London,UK"
    weather_info = openweathermap(location)
    print(f"Weather in {location}: {weather_info}")
