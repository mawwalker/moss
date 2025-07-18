# Moss - 智能语音助手

**🇨🇳 中文 | [🇺🇸 English](README.md)**

---

## 项目简介

Moss 是一个基于现代AI技术的智能语音助手，支持离线关键词唤醒、实时语音识别、智能对话和语音合成。项目采用模块化设计，集成了多种先进的AI服务，包括 Home Assistant MCP 模块，为用户提供自然流畅的语音交互体验。

[![Moss](https://img.youtube.com/vi/usgCC6tQZZg/maxresdefault.jpg)](https://www.youtube.com/watch?v=usgCC6tQZZg)

## 核心特性

🎯 **离线关键词唤醒**
- 支持完全离线的关键词检测
- 可自定义任意唤醒词（中文/英文）
- 基于 sherpa-onnx 的高效模型
- 低功耗持续监听

🗣️ **实时语音识别**
- 基于 WebSocket 的实时STT服务
- 高精度语音转文字
- 支持流式识别，响应迅速
- 参考实现：[stt-server](https://github.com/mawwalker/stt-server)

🤖 **智能对话代理**
- 基于 Langchain Agents 的可扩展架构
- 支持多种工具和技能
- 天气查询、智能家居控制等
- 易于添加自定义工具

🏠 **Home Assistant 集成**
- 基于 MCP (Model Context Protocol) 的智能家居控制
- 无缝对接 Home Assistant 系统
- 支持设备状态查询和控制
- 语音操控智能家居设备

🎵 **高质量语音合成**
- 基于 IndexTTS 的先进TTS技术
- 自然流畅的语音输出
- 参考实现：[index-tts-vllm](https://github.com/Ksuriuri/index-tts-vllm)

## 系统架构

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   关键词检测      │───▶│    语音识别       │───▶│   LLM 处理       │
│ (Offline KWS)   │    │ (Realtime STT)   │    │ (Langchain)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐              │
│   音频播放        │◀───│    语音合成       │◀─────────────┘
│ (Audio Player)  │    │ (IndexTTS)       │
└─────────────────┘    └──────────────────┘
                                ┌─────────────────┐
                                │ Home Assistant  │
                                │  MCP 模块       │
                                └─────────────────┘
```

## 快速开始

### 环境要求

- Python 3.12+
- Linux/macOS/Windows
- 音频设备（麦克风和扬声器）
- Home Assistant（可选，用于智能家居控制）

### 安装依赖

1. 克隆项目及子模块
```bash
git clone https://github.com/your-username/Moss.git
cd Moss
git submodule update --init --recursive
```

2. 安装系统依赖（以Ubuntu为例）
```bash
sudo apt install portaudio19-dev python3-pyaudio sox pulseaudio libsox-fmt-all ffmpeg
```

3. 安装Python依赖
```bash
uv venv
source .venv/bin/activate
uv sync
```

### 配置设置

1. 复制配置文件模板
```bash
cp .env.example .env
```

2. 编辑配置文件，填入必要的API密钥和服务地址

### Home Assistant MCP 模块配置

1. 在 `.env` 文件中配置 Home Assistant 连接信息
```bash
HASS_ENABLE=1
HASS_URL=http://your-home-assistant-url:8123
HASS_TOKEN=your-long-lived-access-token
```

2. 在 Home Assistant 中创建长期访问令牌：
   - 进入 Home Assistant 设置 → 用户 → 安全
   - 创建长期访问令牌
   - 将令牌复制到配置文件中

### 运行程序

```bash
python app.py
```

支持的命令行参数：
```bash
python app.py --help  # 查看所有可用参数
python app.py --verbose  # 启用详细日志
python app.py --keywords-file assets/keywords_en.txt  # 使用英文关键词
```

## Docker 部署

敬请期待

## 扩展功能

### 添加自定义工具

在 `agents/tools.py` 中添加新的工具：

```python
from langchain_core.tools import StructuredTool

def my_custom_tool(param: str):
    """自定义工具功能"""
    return f"处理结果: {param}"

custom_tool = StructuredTool.from_function(
    func=my_custom_tool,
    name="CustomTool",
    description="自定义工具描述"
)

# 在 init_tools() 函数中添加到工具列表
def init_tools() -> list[StructuredTool]:
    tools = [
        openweathermap_tool,
        custom_tool,  # 添加新工具
    ]
    return tools
```

### 自定义唤醒词

https://k2-fsa.github.io/sherpa/onnx/kws/index.html

### Home Assistant MCP 模块

Home Assistant MCP 模块提供了与 Home Assistant 系统的无缝集成：

**支持的功能：**
- 设备状态查询
- 设备开关控制
- 场景激活
- 自动化触发
- 传感器数据读取

**配置说明：**
- 确保 Home Assistant 可访问
- 配置正确的访问令牌
- 网络连接稳定

更多详细配置和使用说明，请参考 [hass-mcp](https://github.com/voska/hass-mcp) 仓库。

## 使用示例

启动程序后，尝试以下语音指令：

- **天气查询**：
  - "莫斯，今天北京的天气怎么样？"
  - "莫斯，查询上海天气"

- **智能家居**（需要配置 Home Assistant）：
  - "莫斯，帮我打开客厅的灯"
  - "莫斯，调高空调温度"
  - "莫斯，关闭所有灯光"
  - "莫斯，查看客厅温度"

- **通用对话**：
  - "莫斯，今天是几号？"
  - "莫斯，讲个笑话"

## 配置说明

### 子模块管理

项目使用 Git 子模块管理 Home Assistant MCP 组件：

```bash
# 更新子模块
git submodule update --remote

# 添加新的子模块
git submodule add https://github.com/example/repo.git path/to/submodule
```

## 注意事项

⚠️ **重要提醒**
- 本项目仍在开发中，可能存在Bug
- Home Assistant MCP 模块需要稳定的网络连接
- 请确保 Home Assistant 访问令牌的安全性

## 贡献指南

我们热烈欢迎各位开发者参与项目建设！

### 贡献方向

- 🔧 **添加新工具**：扩展Agent的功能
- 🌐 **多语言支持**：添加更多语言的支持
- 🐛 **Bug修复**：报告和修复问题
- 📚 **文档完善**：改进项目文档
- 🎨 **界面优化**：改善用户体验
- ⚡ **性能优化**：提升系统效率
- 🏠 **智能家居集成**：扩展 Home Assistant 功能

### 提交指南

提交PR前请确保：
1. 代码符合项目规范
2. 添加必要的测试
3. 更新相关文档
4. 通过现有的测试用例

## 技术栈

- **关键词检测**: sherpa-onnx [Sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx)
- **语音识别**: WebSocket STT ([stt-server](https://github.com/mawwalker/stt-server))
- **语音合成**: IndexTTS ([index-tts-vllm](https://github.com/Ksuriuri/index-tts-vllm))
- **对话引擎**: Langchain Agents
- **智能家居**: Home Assistant MCP ([hass-mcp](https://github.com/voska/hass-mcp))
- **音频处理**: PyAudio, SoX
- **异步框架**: asyncio
- **日志系统**: loguru

## 许可证

本项目采用 GPL-3.0 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 致谢

感谢以下项目的启发：
- [Azure Voice Assistant](https://github.com/DennizSvens/azure-voice-assistant)
- [Wukong Robot](https://github.com/wzpan/wukong-robot)
- [STT Server](https://github.com/mawwalker/stt-server)
- [Index TTS VLLM](https://github.com/Ksuriuri/index-tts-vllm)
- [Home Assistant MCP](https://github.com/voska/hass-mcp)

## 联系我们

- GitHub Issues: [提交问题](https://github.com/your-username/Moss/issues)
- 讨论交流: [Discussions](https://github.com/your-username/Moss/discussions)

---

**欢迎加入我们，共同打造更智能的语音助手！🚀**