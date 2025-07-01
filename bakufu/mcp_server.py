"""
MCP Server implementation for Bakufu AI Workflow Tool.

This module provides the Model Context Protocol (MCP) server functionality,
allowing Bakufu workflows to be executed as MCP tools by compatible clients.
"""

import asyncio
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

from fastmcp import Context, FastMCP

from bakufu.mcp_integration import create_mcp_integrator

logger = logging.getLogger(__name__)

# Global integrator instance
integrator = None
sampling_mode = False


async def initialize_integrator(workflow_dir: Path, config_path: Path) -> None:
    """Initialize the MCP workflow integrator."""
    global integrator
    if integrator is None:
        integrator = create_mcp_integrator(workflow_dir=workflow_dir, config_path=config_path)
        await integrator.initialize()
        logger.info("MCP workflow integrator initialized")
instructions="""
    This is the Bakufu MCP Server, which allows you to execute predefined workflows in Bakufu.
    All workflow tools (except `list_available_workflows`) require a JSON object as input.
    Each workflow has specific input parameters that must be provided.
    
    ## Special Input Prefixes
    
    The Bakufu MCP Server supports powerful prefix-based input processing for flexible data handling:
    
    ### @file: Prefix - File Content Loading
    Syntax: `@file:<path>:<format>:<encoding>`
    - **path** (required): File path (absolute or relative)
    - **format** (optional): Data format - defaults to "text"
    - **encoding** (optional): Character encoding - defaults to "utf-8"
    
    Supported formats:
    - `text` (default): Plain text content as string
    - `lines`: Text content as array of lines
    - `json`: JSON files parsed to objects
    - `yaml`/`yml`: YAML files parsed to objects
    - `csv`: CSV files as array of dictionaries
    - `tsv`: TSV files as array of dictionaries
    
    Examples:
    - `@file:/path/to/document.txt` (plain text, UTF-8)
    - `@file:/data/config.json:json` (JSON format)
    - `@file:/logs/app.log:lines` (text lines array)
    - `@file:/data/report.csv:csv` (CSV as object array)
    - `@file:/path/file.txt:text:shift_jis` (specific encoding)
    
    ### @value: Prefix - JSON Parsing
    Syntax: `@value:<JSON_STRING>`
    Parses JSON strings into their corresponding data types.
    
    Examples:
    - `@value:{"key": "value", "count": 42}` (object)
    - `@value:["item1", "item2", "item3"]` (array)
    - `@value:"simple string"` (string)
    - `@value:42` (number)
    - `@value:true` (boolean)
    
    ### Usage Examples
    
    **Value-based syntax** (prefix in value):
    ```json
    {
        "document": "@file:/path/to/report.txt",
        "settings": "@value:{\"max_length\": 200, \"format\": \"summary\"}",
        "data": "@file:/data/input.json:json"
    }
    ```
    
    **Key-based syntax** (prefix in key):
    ```json
    {
        "@file:document": "/path/to/report.txt:text",
        "@value:settings": "{\"max_length\": 200, \"format\": \"summary\"}",
        "@file:data": "/data/input.json:json"
    }
    ```
    
    Both syntaxes are supported and can be mixed within the same input. These prefixes enable dynamic content loading and structured data input, making workflows more flexible and reusable.
    """

# Create FastMCP server instance
mcp: FastMCP = FastMCP(
    name="bakufu-mcp-server",
    # description for the server.
    # especially prefix treatment like "@file:" & "@value:" is important feature and we must explain it.
    # these are handled by all dynamic tools.
    instructions=instructions,
)

@mcp.tool
async def get_input_specification_text_of_bakufu_tool_execution() -> str:
    """
    Prompt for input specification of a Bakufu tool execution.
    YOU MUST EXECUTE THIS TOOL BEFORE ANY OTHER BAKUFU'S TOOLS.
    """
    return instructions


@mcp.tool
async def list_available_workflows() -> str:
    """
    List all available workflows that can be executed.

    Returns:
        List of available workflows with descriptions
    """
    global integrator
    if integrator is None:
        return "Error: MCP server not initialized"

    try:
        workflows = await integrator.discover_workflows()

        if not workflows:
            return "No workflows found in the workflow directory."

        result = "📋 Available Workflows:\n\n"
        for i, workflow in enumerate(workflows, 1):
            result += f"{i}. **{workflow.name}**\n"
            if workflow.description:
                result += f"   Description: {workflow.description}\n"

            if workflow.input_parameters:
                result += f"   Parameters: {len(workflow.input_parameters)} inputs\n"
                for param in workflow.input_parameters:
                    default_text = (
                        f" (default: {param.default})" if param.default is not None else ""
                    )
                    required_text = " [required]" if param.required else " [optional]"
                    result += f"     - {param.name} ({param.type}){required_text}{default_text}\n"
            else:
                result += "   Parameters: None\n"
            result += "\n"

        return result

    except Exception as e:
        logger.error(f"Error listing workflows: {e}")
        return f"❌ Error listing workflows: {e!s}"


async def register_dynamic_workflow_tools() -> None:
    """Register workflow tools dynamically based on discovered workflows."""
    global integrator
    if integrator is None:
        logger.warning("Cannot register dynamic tools: integrator not initialized")
        return

    try:
        workflows = await integrator.discover_workflows()
        logger.info(f"Discovered {len(workflows)} workflows for dynamic tool registration")

        for workflow in workflows:
            # Create a safe tool name from workflow name
            tool_name = workflow.name.lower().replace(" ", "_").replace("-", "_")
            tool_name = "execute_" + "".join(c for c in tool_name if c.isalnum() or c == "_")

            # Create dynamic tool function with closure over workflow info
            def create_workflow_executor(wf_name: str) -> Callable:
                async def execute_workflow(input: dict, ctx: Context) -> str:
                    """Execute a specific workflow with provided parameters."""
                    global integrator
                    if integrator is None:
                        return "Error: MCP server not initialized"

                    try:
                        # Validate input is a dictionary
                        if not isinstance(input, dict):
                            return f"❌ Input must be a JSON object, got {type(input).__name__}"

                        # Pass MCP context and sampling mode to integrator
                        result = await integrator.execute_workflow(
                            workflow_name=wf_name,
                            input_arguments=input,
                            mcp_context=ctx if sampling_mode else None,
                            sampling_mode=sampling_mode,
                        )

                        if result.success:
                            response = f"✅ Workflow '{wf_name}' completed successfully!\n\n{result.result}"
                            if result.execution_time:
                                response += (
                                    f"\n\n⏱️ Execution time: {result.execution_time:.2f} seconds"
                                )
                            if result.usage_summary:
                                usage = result.usage_summary
                                response += f"\n📊 AI Usage: {usage['total_api_calls']} calls, {usage['total_tokens']} tokens, ${usage['total_cost_usd']:.6f}"
                            return response
                        else:
                            return f"❌ Workflow '{wf_name}' failed: {result.error_message}"

                    except Exception as e:
                        logger.error(f"Error executing workflow {wf_name}: {e}")
                        return f"❌ Unexpected error: {e!s}"

                return execute_workflow

            # Create the function with proper closure
            tool_func = create_workflow_executor(workflow.name)

            # Set function metadata
            tool_func.__name__ = tool_name
            tool_description = f"Execute workflow: {workflow.name}"
            if workflow.description:
                tool_description += f"\n\n{workflow.description}"

            # Add input format information to description
            tool_description += "\n\nInput: JSON object with the following parameters:"
            if workflow.input_parameters:
                for param in workflow.input_parameters:
                    required_text = " (required)" if param.required else " (optional)"
                    default_text = (
                        f" [default: {param.default}]" if param.default is not None else ""
                    )
                    tool_description += (
                        f"\n- {param.name} ({param.type}){required_text}{default_text}"
                    )
                    if param.description:
                        tool_description += f": {param.description}"
            else:
                tool_description += "\n- No parameters required (empty object: {})"

            tool_func.__doc__ = tool_description

            # Use the tool decorator to register dynamically
            mcp.tool(tool_func, name=tool_name, description=tool_description)
            logger.info(f"Registered dynamic tool: {tool_name} for workflow: {workflow.name}")

    except Exception as e:
        logger.error(f"Error registering dynamic workflow tools: {e}")


async def main_async() -> None:
    """Async main entry point for the MCP server."""
    import argparse

    parser = argparse.ArgumentParser(description="Bakufu MCP Server")
    parser.add_argument(
        "--workflow-dir",
        type=Path,
        default=Path("examples/en/basic"),
        help="Directory containing workflow files",
    )
    parser.add_argument(
        "--config", type=Path, default=Path("bakufu.yml"), help="Path to configuration file"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--sampling-mode",
        action="store_true",
        help="Use MCP sampling instead of LLM providers",
    )

    args = parser.parse_args()

    # Set global sampling mode
    global sampling_mode
    sampling_mode = args.sampling_mode

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Initialize integrator
    await initialize_integrator(args.workflow_dir, args.config)

    # Register dynamic workflow tools
    await register_dynamic_workflow_tools()

    logger.info(f"Starting Bakufu MCP Server from {args.workflow_dir}")

    # Run the MCP server
    await mcp.run_stdio_async()


def main() -> None:
    """Synchronous entry point for the MCP server (for script entry points)."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
