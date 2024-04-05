import json
import requests
from loguru import logger
from langchain.pydantic_v1 import BaseModel
from langchain.agents import tool, Tool, initialize_agent, load_tools
from langchain.tools import BaseTool, StructuredTool, tool
from langchain_community.utilities import OpenWeatherMapAPIWrapper
from config.conf import config

hass_url = config['agent_config']['hass']['host']
hass_port = config['agent_config']['hass']['port']
hass_headers = {'Authorization': config['agent_config']['hass']['key'], 'content-type': 'application/json'}


class BrightnessControlInput(BaseModel):
    entity_id: str 
    brightness_pct: int
    
class FeederOutInput(BaseModel):
    entity_id: str
    nums: int

class HvacControlInput(BaseModel):
    entity_id: str
    input_dict: dict

class OpenWeatherMapInput(BaseModel):
    location_code: str

def brightness_control(entity_id, brightness_pct):
    data = {"entity_id": entity_id,
            "brightness_pct": brightness_pct
    }
    p = json.dumps(data)
    domain = entity_id.split(".")[0]
    s = "/api/services/" + domain + "/"
    url_s = hass_url + ":" + hass_port + s + "turn_on"
    request = requests.post(url_s, headers=hass_headers, data=p)
    if format(request.status_code) == "200" or \
        format(request.status_code) == "201": 
        return True
    else:
        logger.error(format(request))
        return False

def hvac_control(entity_id, input_dict:dict):
    data = {"entity_id": entity_id
            }
    operation = input_dict['operation']
    if input_dict.get("hvac_mode"):
        data["hvac_mode"] = input_dict.get("hvac_mode")
    if input_dict.get("temperature"):
        data["temperature"] = input_dict.get("temperature")
    if input_dict.get("fan_mode"):
        data["fan_mode"] = input_dict.get("fan_mode")
    p = json.dumps(data)
    domain = entity_id.split(".")[0]
    s = "/api/services/" + domain + "/"
    url_s = hass_url + ":" + hass_port + s + operation
    logger.info(f"url_s: {url_s}, data: {p}")
    request = requests.post(url_s, headers=hass_headers, data=p)
    if format(request.status_code) == "200" or \
        format(request.status_code) == "201": 
        return True
    else:
        logger.error(format(request))
        return False

def feeder_out(entity_id, nums):
    domain = entity_id.split(".")[0]
    s = "/api/services/" + domain + "/"
    url_s = hass_url + ":" + hass_port + s + "turn_on"
    data = {
        "entity_id": entity_id,
        "variables": {"nums": nums}
    }
    p = json.dumps(data)
    request = requests.post(url_s, headers=hass_headers, data=p)
    if format(request.status_code) == "200" or \
        format(request.status_code) == "201": 
        return True
    else:
        logger.error(format(request))
        return False

def get_attributes(entity_id):
    url_entity = hass_url + ":" + hass_port + "/api/states/" + entity_id
    device_state = requests.get(url_entity, headers=hass_headers).json()
    attributes = device_state['attributes']
    return attributes

def openweathermap(location_code):
    weather = OpenWeatherMapAPIWrapper()
    weather_data = weather.run(location_code)
    return weather_data

brightness_control_tool = StructuredTool(
    name="brightness_control",
    description="Control the brightness of a light. the brightness_pct must be between 10 and 100 for ajust brightness, set it to 0 to turn off the light. input: brightness_pct: int, entity_id: str, output: bool.s",
    func=brightness_control,
    args_schema=BrightnessControlInput
)

feeder_out_tool = StructuredTool(
    name="feeder_out",
    description="Control the pet feeder. You can Only use this tool when you need to feed. The nums must be between 1 and 10, input: nums: int, entity_id: str, output: bool.",
    func=feeder_out,
    args_schema=FeederOutInput
)

get_attr_tool = Tool(
    name="get_attributes",
    description="Get the attributes of a device. input: entity_id: str, output: dict.",
    func=get_attributes
)

hvac_control_tool = StructuredTool(
    name="hvac_control",
    description="""Control the hvac. input: entity_id: str, input_dict: dict, output: bool. input_dict include: operation must in (set_hvac_mode, set_fan_mode, set_temperature), 
    hvac_mode must in (off, auto, cool, heat, dry, fan_only), temperature(int type), fan_mode must in ('Fan Speed Down', 'Fan Speed Up'), You must choose at least one operation and Pass the corresponding parameter (ONLY ONE) as needed.
    """,
    func=hvac_control,
    args_schema=HvacControlInput
)

openweathermap_api = StructuredTool(
    name="openweathermap-api",
    description="""This tool fetches weather data from OpenWeatherMap API. Input is a location code In English ONLY. For example, "London", "London,UK" or "London,GB" for London, United Kingdom.
    """,
    func=openweathermap,
    args_schema=OpenWeatherMapInput
)