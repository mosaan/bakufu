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

from fastmcp import FastMCP

from bakufu.mcp_integration import create_mcp_integrator

logger = logging.getLogger(__name__)

# Global integrator instance
integrator = None


async def initialize_integrator(workflow_dir: Path, config_path: Path) -> None:
    """Initialize the MCP workflow integrator."""
    global integrator
    if integrator is None:
        integrator = create_mcp_integrator(workflow_dir=workflow_dir, config_path=config_path)
        await integrator.initialize()
        logger.info("MCP workflow integrator initialized")


# Create FastMCP server instance
mcp: FastMCP = FastMCP(name="bakufu-mcp-server")


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
            def create_workflow_executor(wf_name: str, wf_params: Any) -> Callable:
                async def execute_workflow(input: dict) -> str:
                    """Execute a specific workflow with provided parameters."""
                    global integrator
                    if integrator is None:
                        return "Error: MCP server not initialized"

                    try:
                        # Validate input is a dictionary
                        if not isinstance(input, dict):
                            return f"❌ Input must be a JSON object, got {type(input).__name__}"

                        result = await integrator.execute_workflow(
                            workflow_name=wf_name, input_arguments=input
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
            tool_func = create_workflow_executor(workflow.name, workflow.input_parameters)

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

    args = parser.parse_args()

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
