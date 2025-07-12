# Moss - Intelligent Voice Assistant

**[🇨🇳 中文](README_zh.md) | 🇺🇸 English**

---

## Project Overview

Moss is an intelligent voice assistant built with modern AI technologies, featuring offline keyword wake-up, real-time speech recognition, intelligent conversation, and speech synthesis. The project uses a modular design and integrates various advanced AI services, including Home Assistant MCP module, to provide users with natural and smooth voice interaction experiences.

[![Moss](https://img.youtube.com/vi/usgCC6tQZZg/maxresdefault.jpg)](https://www.youtube.com/watch?v=usgCC6tQZZg)

## Key Features

🎯 **Offline Keyword Wake-up**
- Complete offline keyword detection
- Customizable wake words (Chinese/English)
- Efficient sherpa-onnx based models
- Low-power continuous listening

🗣️ **Real-time Speech Recognition**
- WebSocket-based real-time STT service
- High-precision speech-to-text
- Streaming recognition for quick response
- Reference implementation: [stt-server](https://github.com/mawwalker/stt-server)

🤖 **Intelligent Conversation Agent**
- Extensible architecture based on Langchain Agents
- Support for multiple tools and skills
- Weather queries, smart home control, etc.
- Easy to add custom tools

🏠 **Home Assistant Integration**
- Smart home control based on MCP (Model Context Protocol)
- Seamless integration with Home Assistant system
- Device status queries and control
- Voice control of smart home devices

🎵 **High-quality Speech Synthesis**
- Advanced TTS technology based on IndexTTS
- Natural and fluent voice output
- Reference implementation: [index-tts-vllm](https://github.com/Ksuriuri/index-tts-vllm)

## System Architecture

```
┌──────────────────┐    ┌───────────────────┐    ┌─────────────────┐
│ Keyword Detection│───▶│ Speech Recognition│───▶│  LLM Processing │
│   (Offline KWS)  │    │  (Realtime STT)   │    │  (Langchain)    │
└──────────────────┘    └───────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐              │
│  Audio Playback │◀───│ Speech Synthesis │◀─────────────┘
│ (Audio Player)  │    │   (IndexTTS)     │
└─────────────────┘    └──────────────────┘
                               ┌─────────────────┐
                               │ Home Assistant  │
                               │   MCP Module    │
                               └─────────────────┘
```

## Quick Start

### Requirements

- Python 3.12+
- Linux/macOS/Windows
- Audio devices (microphone and speakers)
- Home Assistant (optional, for smart home control)

### Installation

1. Clone the repository with submodules
```bash
git clone https://github.com/your-username/Moss.git
cd Moss
git submodule update --init --recursive
```

2. Install system dependencies (Ubuntu example)
```bash
sudo apt install portaudio19-dev python3-pyaudio sox pulseaudio libsox-fmt-all ffmpeg
```

3. Install Python dependencies
```bash
uv venv
source .venv/bin/activate
uv sync
```

### Configuration

1. Copy configuration template
```bash
cp .env.example .env
```

2. Edit the configuration file with necessary API keys and service addresses

### Home Assistant MCP Module Configuration

1. Configure Home Assistant connection in `.env` file
```bash
HASS_ENABLE=1
HASS_URL=http://your-home-assistant-url:8123
HASS_TOKEN=your-long-lived-access-token
```

2. Create a long-lived access token in Home Assistant:
   - Go to Home Assistant Settings → Users → Security
   - Create a long-lived access token
   - Copy the token to your configuration file

### Running the Application

```bash
python app.py
```

Supported command line arguments:
```bash
python app.py --help  # View all available parameters
python app.py --verbose  # Enable verbose logging
python app.py --keywords-file assets/keywords_en.txt  # Use English keywords
```

## Docker Deployment

Coming soon

## Extending Features

### Adding Custom Tools

Add new tools in `agents/tools.py`:

```python
from langchain_core.tools import StructuredTool

def my_custom_tool(param: str):
    """Custom tool functionality"""
    return f"Processing result: {param}"

custom_tool = StructuredTool.from_function(
    func=my_custom_tool,
    name="CustomTool",
    description="Custom tool description"
)

# Add to tools list in init_tools() function
def init_tools() -> list[StructuredTool]:
    tools = [
        openweathermap_tool,
        custom_tool,  # Add new tool
    ]
    return tools
```

### Custom Wake Words

https://k2-fsa.github.io/sherpa/onnx/kws/index.html

### Home Assistant MCP Module

The Home Assistant MCP module provides seamless integration with Home Assistant systems:

**Supported Features:**
- Device status queries
- Device on/off control
- Scene activation
- Automation triggers
- Sensor data reading

**Configuration Notes:**
- Ensure Home Assistant is accessible
- Configure correct access token
- Stable network connection required

For detailed configuration and usage instructions, please refer to the [hass-mcp](https://github.com/voska/hass-mcp) repository.

## Usage Examples

After starting the program, try these voice commands:

- **Weather Queries**:
  - "Moss, what's the weather like in Beijing today?"
  - "Moss, check weather in Tokyo"

- **Smart Home** (requires Home Assistant configuration):
  - "Moss, turn on the living room light"
  - "Moss, increase the air conditioner temperature"
  - "Moss, turn off all lights"
  - "Moss, check the living room temperature"

- **General Conversation**:
  - "Moss, what's today's date?"
  - "Moss, tell me a joke"

## Configuration

### Submodule Management

The project uses Git submodules to manage Home Assistant MCP components:

```bash
# Update submodules
git submodule update --remote

# Add new submodule
git submodule add https://github.com/example/repo.git path/to/submodule
```

## Important Notes

⚠️ **Important Reminders**
- This project is still under development and may contain bugs
- Home Assistant MCP module requires stable network connection
- Ensure the security of Home Assistant access tokens

## Contributing

We warmly welcome developers to participate in building this project!

### Contribution Areas

- 🔧 **Add New Tools**: Extend Agent capabilities
- 🌐 **Multi-language Support**: Add support for more languages
- 🐛 **Bug Fixes**: Report and fix issues
- 📚 **Documentation**: Improve project documentation
- 🎨 **UI/UX**: Enhance user experience
- ⚡ **Performance**: Optimize system efficiency
- 🏠 **Smart Home Integration**: Extend Home Assistant functionality

### Submission Guidelines

Before submitting a PR, please ensure:
1. Code follows project standards
2. Add necessary tests
3. Update relevant documentation
4. Pass existing test cases

## Tech Stack

- **Keyword Detection**: sherpa-onnx [Sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx)
- **Speech Recognition**: WebSocket STT ([stt-server](https://github.com/mawwalker/stt-server))
- **Speech Synthesis**: IndexTTS ([index-tts-vllm](https://github.com/Ksuriuri/index-tts-vllm))
- **Conversation Engine**: Langchain Agents
- **Smart Home**: Home Assistant MCP ([hass-mcp](https://github.com/voska/hass-mcp))
- **Audio Processing**: PyAudio, SoX
- **Async Framework**: asyncio
- **Logging**: loguru

## Dependencies & References

- **STT Service**: [stt-server](https://github.com/mawwalker/stt-server)
- **TTS Service**: [index-tts-vllm](https://github.com/Ksuriuri/index-tts-vllm)
- **Langchain**: [Official Documentation](https://python.langchain.com/)
- **Sherpa-ONNX**: [Keyword Spotting](https://github.com/k2-fsa/sherpa-onnx)
- **Home Assistant MCP**: [hass-mcp](https://github.com/voska/hass-mcp)

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

Thanks to the following projects for inspiration:
- [Sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx)
- [STT Server](https://github.com/mawwalker/stt-server)
- [Index TTS VLLM](https://github.com/Ksuriuri/index-tts-vllm)
- [Home Assistant MCP](https://github.com/voska/hass-mcp)

## Contact Us

- GitHub Issues: [Submit Issues](https://github.com/your-username/Moss/issues)
- Discussions: [Discussions](https://github.com/your-username/Moss/discussions)

---

**Join us in building a more intelligent voice assistant! 🚀**