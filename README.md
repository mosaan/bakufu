# 🌊 bakufu

**AI-Powered Workflow Automation CLI Tool**

bakufu (瀑布, "great waterfall" in Japanese) is a powerful workflow automation tool powered by AI. The name is inspired by the continuous flow of AI calls resembling the relentless force of a waterfall. Define workflows in YAML and combine multiple AI providers with text processing capabilities to automate complex tasks.

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## ✨ Key Features

### 🤖 AI Provider Integration
- **LiteLLM backed**: Multiple AI provider integration using LiteLLM
- **MCP Sampling Support**: Use GitHub Copilot's LLM via Model Context Protocol
- **Dual Mode Operation**: Switch between traditional providers and MCP sampling

### 📝 Text Processing Capabilities
- **Regex Extraction** - Data extraction through pattern matching
- **Text Replacement** - String and regex-based transformations
- **JSON Parsing** - Structured data analysis with schema validation
- **Markdown Splitting** - Section-based document processing

### 🔤 Basic Text Methods
- **split** - Split strings with custom separators and limits
- **extract_between_marker** - Extract text between specified markers  
- **select_item** - Select array elements by index, slice, or condition
- **parse_as_json** - Parse JSON with validation and metadata

### 📊 Collection Operations
- **map** - Transform each element in a collection using AI or text processing
- **filter** - Select elements that match specified conditions
- **reduce** - Aggregate collection elements into a single value
- **pipeline** - Chain multiple collection operations together
- **Parallel Processing** - Concurrent execution with configurable concurrency
- **Error Handling** - Flexible strategies for handling failures (skip, stop, retry)

### 🔀 Conditional Operations
- **conditional** - Execute different steps based on dynamic conditions
- **if-else Structure** - Simple true/false branch execution
- **Multi-branch Logic** - Complex condition evaluation with multiple paths
- **Error Handling** - Configurable strategies for condition evaluation failures
- **Nested Support** - Conditional steps within conditional branches
- **Template Integration** - Jinja2-based condition evaluation with full context access

### ✅ AI Output Validation
- **JSON Schema Validation** - Ensure AI outputs match defined schemas
- **Pydantic Model Validation** - Type-safe validation using Pydantic models
- **Custom Validation Functions** - Flexible validation with custom logic
- **Automatic Retry Logic** - Smart retry with validation-aware prompts
- **Output Recovery** - Extract valid data from malformed AI responses
- **Parallel Validation** - Works seamlessly with AI map operations

### 🔧 Advanced Features
- **Jinja2 Templates** - Dynamic workflow execution
- **Error Handling** - Detailed error information and recovery suggestions
- **Parallel Execution** - Efficient task processing with AI Map Call
- **Real-time Progress Display** - Visual progress bars and execution monitoring
- **Rich Configuration Options** - Fine-grained provider-specific adjustments

### 🔌 MCP (Model Context Protocol) Integration
- **MCP Server** - Run bakufu workflows as MCP tools for compatible clients
- **Sampling Mode** - Use GitHub Copilot's LLM via MCP sampling API (no API key required)
- **Dynamic Tool Registration** - Automatically expose all workflows as individual MCP tools
- **Dual Mode Support** - Switch between traditional LLM providers and MCP sampling
- **Unified Input Processing** - Support for `@file:` and `@value:` prefixes in MCP tool parameters
- **Client Compatibility** - Works with Claude Desktop, Cursor, GitHub Copilot, and other MCP-compatible applications
- **Real-time Workflow Discovery** - Automatic detection and registration of new workflows

## 🚀 Quick Start

### Installation

```bash
uv tool install git+https://github.com/mosaan/bakufu.git
```

### Basic Usage

1. **Initialize Configuration**
```bash
# Create basic configuration
bakufu config init

# Set API keys
export GOOGLE_API_KEY="your_gemini_api_key"
```

2. **Run Your First Workflow**
```bash
# Run Hello World sample
bakufu run examples/en/basic/hello-world.yml --input '{"name": "John"}'

# Try text summarization
bakufu run examples/en/basic/text-summarizer.yml --input '{
  "text": "Your long text here...", 
  "max_length": 200
}'
```

3. **Validate Workflows**
```bash
# Check YAML syntax
bakufu validate examples/en/basic/hello-world.yml

# Detailed validation
bakufu validate --verbose my-workflow.yml
```

see [docs](docs/README.md) for more details.

## 🔌 MCP Server Usage

### GitHub Copilot Integration

Use bakufu workflows directly in GitHub Copilot with MCP sampling mode:

```bash
# Start MCP server with sampling mode (no API key required)
bakufu-mcp --workflow-dir examples/ja/basic --config bakufu.yml --sampling-mode --verbose
```

Then in GitHub Copilot Chat:
```
@bakufu-mcp-sampling execute_mcp_test {"message": "Hello from Copilot!"}
@bakufu-mcp-sampling execute_code_review {"code": "def hello():\n    print('world')", "language": "python"}
```

### Traditional LLM Providers

Use with your own API keys for Gemini, OpenAI, etc.:

```bash
# Standard mode with LiteLLM providers
bakufu-mcp --workflow-dir examples/ja/basic --config bakufu.yml --verbose
```

See [MCP_SETUP.md](./MCP_SETUP.md) for detailed setup instructions.

## 🔧 Developer Information

## 🤝 Contributing

Contributions are very welcome! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for details.

### Bug Reports & Feature Requests

Feel free to let us know via [GitHub Issues](https://github.com/mosaan/bakufu/issues).

### Participate in Development

1. Fork and create a branch
2. Implement changes
3. Add and run tests
4. Create Pull Request

## 📄 License

MIT License - See [LICENSE](./LICENSE) file for details.

## 🙏 Acknowledgments

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) - Primary Coder
- [LiteLLM](https://github.com/BerriAI/litellm) - AI provider integration
- [Jinja2](https://jinja.palletsprojects.com/) - Template engine
- [Pydantic](https://pydantic.dev/) - Data validation
- [Click](https://click.palletsprojects.com/) - CLI framework

---

**Start simple AI-powered workflow automation with bakufu!** 🚀