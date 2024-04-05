# Voice Assistant with Azure Cognitive Speech Services, Azure OpenAI and Langchain

I built a voice assistant using Azure Cognitive Speech Services, Azure OpenAI and Langchain Agents.
The voice assistant can perform a variety of tasks such as searching the web, answering the weather, 
controling your home assistant.

The voice assistant use Langchain Agents to perform the tasks. You can easily add more tools by adding tools to load_tools(). 

You can Add your own tools in the agents/tools.py

Read more about Langchain and Langchain agents/tools here: 

https://python.langchain.com/en/latest/modules/agents.html

https://python.langchain.com/docs/modules/tools/custom_tools/

## Attention
**This project is still in development and may contain bugs.** Please report any issues you encounter.
If You use this project to control your home assistant or do other important things, please be careful.

**This project and the author are not responsible for any damage caused by the use of this project.**

## Prerequisites

- Azure account
- Azure Keyword Recognition Model: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/custom-keyword-basics?pivots=programming-language-python
- Azure Speech Service: https://learn.microsoft.com/en-us/azure/cognitive-services/speech-service/
- Azure OpenAI Service: https://azure.microsoft.com/en-us/products/cognitive-services/openai-service
- Openweather API: https://openweathermap.org/api
- Google Custom Json Search API: https://developers.google.com/custom-search/v1/overview
- Home Assistant: https://www.home-assistant.io/

## Setup
###  On Linux
**Recommended System with Openssl < 3 installed.** 

Because Azure Speech Service requires Openssl < 3 Yet(2024.04.05).

Refer to This Issue: https://github.com/Azure-Samples/cognitive-services-speech-sdk/issues/2048

And the Azure Speech Service Documentation: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/quickstarts/setup-platform

1. Clone this repository to your local machine.

2. Install the required dependencies:

Install the System packages with Your Package Manager, this is an example for Ubuntu/Debian based systems. You can install the packages with your package manager:
```
portaudio19-dev python3-pyaudio sox pulseaudio libsox-fmt-all ffmpeg wget libpcre3 libpcre3-dev libatlas-base-dev python3-dev
```
Install the python packages with pip:
```bash
pip install -r requirements.txt
```

1. Copy the config.example.yaml to config.yaml and fill in the required information.

2. Run the script: 
```bash
python app.py
```

### Using Docker
1. Clone this repository to your local machine.
2. Copy the config.example.yaml to config.yaml and fill in the required information.
3. Build the Docker image:
```bash
docker build -t moss:latest .
```
1. Run the Docker container:
```bash
docker run -itd --device /dev/snd -v ./:/moss --name moss moss:latest
```

## Basic Usage
Once the voice assistant is running, it will continuously listen for the wakeup keyword "莫斯"(In Chinese) or "Moss"(In English). Once the keyword is detected, it will start listening for speech input, which it will then pass to the OpenAI model for processing. The model's response will be spoken out loud using Edge-TTS.

## Extending the Voice Assistant tools
The voice assistant can be extended by adding more tools to the `load_tools()` function in `agents/tools.py`. I use StructuredTool to add tools to the voice assistant. 

You can also use class to add tools to the voice assistant, that each tool should be a class that inherits from `BaseTool` and implements the `run` method. The `run` method should return a string that will be spoken out loud by the voice assistant.

Learn more about Langchain Agents and Tools here: https://python.langchain.com/en/latest/modules/agents.html

### Examples

Once the voice assistant is running, you can use the following example prompts to interact with it:

* "Moss, How It's the weather in Beijing?"
* "Moss, Turn on the light"

It can also respond to any general queries that the GPT model is capable of answering. However, its capabilities extend beyond that.

## Contributions
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the GPL-3.0 License - see the LICENSE file for details.

## Thanks
Thanks to the following repositories for inspiration:
- https://github.com/DennizSvens/azure-voice-assistant
- https://github.com/wzpan/wukong-robot