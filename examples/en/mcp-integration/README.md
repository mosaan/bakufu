# MCP Integration Examples

This directory contains workflow examples specifically designed to demonstrate bakufu's Model Context Protocol (MCP) integration capabilities.

## Available Workflows

### 1. Document Analyzer (`document-analyzer.yml`)
Analyzes documents with flexible input formats using MCP's unified input processing.

**Features:**
- Supports `@file:` prefix for loading documents
- Handles multiple document formats (text, JSON, markdown)
- Provides structured analysis output

**MCP Usage:**
```
User: Analyze the document at /path/to/document.txt
Assistant: [Uses execute_document_analyzer with document="@file:/path/to/document.txt"]
```

### 2. Multi-Source Content Creator (`multi-source-content-creator.yml`)
Creates content by combining data from multiple sources using MCP's advanced input processing.

**Features:**
- Combines file inputs with direct JSON values
- Demonstrates `@value:` prefix usage
- Shows complex parameter handling

**MCP Usage:**
```
User: Create a report using data.json and requirements.txt
Assistant: [Uses execute_multi_source_content_creator with:
  - data_source="@file:/path/to/data.json:json"
  - requirements="@file:/path/to/requirements.txt"
  - output_format="@value:{\"type\": \"report\", \"style\": \"professional\"}"
]
```

### 3. Interactive File Processor (`file-processor.yml`)
Processes files interactively with various operations, perfect for MCP tool usage.

**Features:**
- Multiple processing operations (summarize, extract, transform)
- Dynamic operation selection
- File format auto-detection

**MCP Usage:**
```
User: Extract key information from /path/to/file.pdf
Assistant: [Uses execute_interactive_file_processor with:
  - file_path="@file:/path/to/file.pdf"
  - operation="extract"
  - output_format="key_points"
]
```

## Getting Started

1. **Start the MCP Server:**
   ```bash
   python -m bakufu.mcp_server --workflow-dir examples/en/mcp-integration
   ```

2. **Configure Your MCP Client:**
   Add the bakufu server to your MCP client configuration (e.g., Claude Desktop).

3. **Use the Tools:**
   The workflows will be available as MCP tools in your client application.

## Unified Input Format Examples

These workflows demonstrate bakufu's unified input format:

- **File Loading**: `@file:path/to/file.ext:format:encoding`
- **JSON Values**: `@value:{"key": "value"}`
- **Direct Values**: Regular strings and numbers work as-is

## Tips for MCP Usage

1. **File Paths**: Use absolute paths for `@file:` prefixes
2. **JSON Escaping**: Properly escape JSON in `@value:` prefixes
3. **Error Handling**: Workflows include comprehensive error handling for MCP scenarios
4. **Documentation**: Each workflow has detailed parameter descriptions for MCP clients