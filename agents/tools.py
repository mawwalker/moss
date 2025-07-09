from langchain_core.tools import StructuredTool
from langchain.pydantic_v1 import BaseModel
from langchain_community.utilities import OpenWeatherMapAPIWrapper
from loguru import logger
from config.conf import openweather_api_key


class OpenWeatherMapInput(BaseModel):
    location_code: str
    

def openweathermap(location_code):
    logger.info(f"Fetching weather data for location: {location_code}")
    weather = OpenWeatherMapAPIWrapper(openweathermap_api_key=openweather_api_key)
    weather_data = weather.run(location_code)
    logger.info(f"Weather data fetched: {weather_data}")
    return weather_data

openweathermap_tool = StructuredTool.from_function(
    func=openweathermap,
    name="openweathermap",
    description="""This tool fetches weather data from OpenWeatherMap API. Input is a location code In English ONLY. For example, "London", "London,UK" or "London,GB" for London, United Kingdom.
    """,
    args_schema=OpenWeatherMapInput
)


def init_tools() -> list[StructuredTool]:
    """Initialize and return a list of tools for the agent."""
    tools = [
        openweathermap_tool,
        # Add other tools here as needed
    ]
    return tools


if __name__ == "__main__":
    # Test the OpenWeatherMap tool
    location = "London,UK"
    weather_info = openweathermap(location)
    print(f"Weather in {location}: {weather_info}")