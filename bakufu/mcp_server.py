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


instructions = """
    This is the Bakufu MCP Server, which allows you to execute predefined workflows in Bakufu.
    All workflow tools (except `list_available_workflows`) require a JSON object as input.
    Each workflow has specific input parameters that must be provided.
    
    ## Large Output Control
    
    The Bakufu MCP Server provides two methods to handle large workflow outputs:
    
    ### Method 1: Explicit File Output
    For workflows that may produce large outputs, you can specify an output file path as a separate tool argument:
    - input: {"param1": "value1", "param2": "value2"}
    - output_file_path: "/path/to/output.txt"
    
    When provided, results will be saved to the specified file instead of being returned directly.
    Note: output_file_path is a separate tool argument, independent of workflow input parameters.
    
    ### Method 2: Automatic File Output
    Large outputs (>8,000 characters by default) are automatically saved to files.
    The server will return a message indicating where the file was saved (as absolute path).
    If automatic file saving fails, the full text output will be returned with a warning (no truncation).
    
    ## Special Input Prefixes
    
    The Bakufu MCP Server supports powerful prefix-based input processing for flexible data handling.
    if you want to change the input treatment, you can use the following prefixes in your input keys:
    
    ### @file: Prefix - File Content Loading
    Syntax: `{"@file:<key>": "<path>:<format>:<encoding>"}`
    
    Supported formats:
    - `json`: (default for `.json` files) JSON files parsed to objects
    - `yaml`/`yml`: (default for `.yaml`/`.yml` files) YAML files parsed to objects
    - `csv`: (default for `.csv` files) CSV files as array of dictionaries
    - `tsv`: (default for `.tsv` files) TSV files as array of dictionaries
    - `text`: (default for all other unknown file extensions) Plain text content as string
    - `lines`: Text content as array of lines
    
    Examples:
    - `{"@file:document": "/path/to/file.txt"}` (plain text, UTF-8)
    - `{"@file:config": "/data/config.json:json"}` (JSON format)
    - `{"@file:logs": "/logs/app.log:lines"}` (text lines array)
    - `{"@file:data": "/data/report.csv:csv"}` (CSV as object array)
    - `{"@file:content": "/path/file.txt:text:shift_jis"}` (specific encoding)

    ### Direct JSON Values
    You can pass JSON values directly without any special prefix.
    
    Examples:
    - `{"settings": {"key": "value", "count": 42}}` (object)
    - `{"items": ["item1", "item2", "item3"]}` (array)
    - `{"message": "simple string"}` (string)
    - `{"count": 42}` (number)
    - `{"enabled": true}` (boolean)

    ### Usage Examples
    
    **Basic Usage**:
    ```json
    {
        "@file:document": "/path/to/report.txt:text",
        "settings": {"max_length": 200, "format": "summary"},
        "@file:data": "/data/input.json:json"
    }
    ```
    
    **With File Output**:
    ```json
    {
        "@file:document": "/path/to/report.txt:text",
        "settings": {"max_length": 200, "format": "summary"}
    }
    
    And if you want to save large output to a file, use the separate output_file_path parameter:
    - output_file_path: "/path/to/results.txt"
    ```
    
    This syntax enables dynamic content loading, structured data input, and flexible output management, making workflows more powerful and scalable.
    """

# Create FastMCP server instance
mcp: FastMCP = FastMCP(
    name="bakufu-mcp-server",
    # description for the server.
    # especially prefix treatment like "@file:" is important feature and we must explain it.
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
            # Create tool name from workflow name (convert hyphens to underscores for MCP compatibility)
            tool_name = "execute_" + workflow.name.replace("-", "_")

            # Create dynamic tool function with closure over workflow info
            def create_workflow_executor(wf_name: str) -> Callable:
                async def execute_workflow(
                    input: dict, output_file_path: str | None = None, *, ctx: Context
                ) -> str:
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
                            output_file_path=output_file_path,
                            mcp_context=ctx if sampling_mode else None,
                            sampling_mode=sampling_mode,
                        )

                        if result.success:
                            # Format output according to workflow configuration
                            formatted_result = await _format_mcp_output(
                                result.result, wf_name, integrator, input
                            )

                            response = f"✅ Workflow '{wf_name}' completed successfully!\n\n{formatted_result}"
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
            tool_description += "\n\nParameters:"
            tool_description += (
                "\n\n1. input (object): JSON object with workflow-specific parameters:"
            )
            if workflow.input_parameters:
                for param in workflow.input_parameters:
                    required_text = " (required)" if param.required else " (optional)"
                    default_text = (
                        f" [default: {param.default}]" if param.default is not None else ""
                    )
                    tool_description += (
                        f"\n   - {param.name} ({param.type}){required_text}{default_text}"
                    )
                    if param.description:
                        tool_description += f": {param.description}"
            else:
                tool_description += (
                    "\n   - No workflow-specific parameters required (empty object: {})"
                )

            tool_description += "\n\n2. output_file_path (string, optional): File path to save large outputs. When provided, results will be saved to this file instead of being returned directly. Useful for workflows that generate large outputs."

            tool_func.__doc__ = tool_description

            # Use the tool decorator to register dynamically
            mcp.tool(tool_func, name=tool_name, description=tool_description)
            logger.info(f"Registered dynamic tool: {tool_name} for workflow: {workflow.name}")

    except Exception as e:
        logger.error(f"Error registering dynamic workflow tools: {e}")


async def _format_mcp_output(
    result: dict[str, Any] | str, workflow_name: str, integrator: Any, input_data: dict[str, Any]
) -> str:
    """
    Format workflow execution result according to workflow's output configuration.

    This function applies the same formatting logic as the CLI mode to ensure
    consistent output formatting across different execution modes.
    """
    import json

    # Get workflow definition to access output configuration
    workflow_def = await integrator._get_workflow_definition(workflow_name)
    if workflow_def is None:
        # Fallback to simple string conversion if workflow not found
        return str(result)

    # Apply the same formatting logic as CLI _format_output function
    if workflow_def.output and workflow_def.output.template and isinstance(result, dict):
        # Use template engine to format output
        try:
            from bakufu.core.template_engine import WorkflowTemplateEngine

            engine = WorkflowTemplateEngine()
            context = {"steps": result, "input": input_data or {}}
            return engine.render(workflow_def.output.template, context)
        except Exception as e:
            logger.error(f"Error rendering template for workflow {workflow_name}: {e}")
            # Fallback to JSON formatting
            return json.dumps(result, indent=2, ensure_ascii=False)
    elif isinstance(result, dict) and len(result) == 1:
        # Single-key dictionary: return just the value
        return str(next(iter(result.values())))
    elif isinstance(result, str):
        # Already a string
        return result
    else:
        # Default to JSON formatting
        return json.dumps(result, indent=2, ensure_ascii=False)


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
