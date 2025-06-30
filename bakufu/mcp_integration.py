"""
MCP Integration Layer for Bakufu.

This module provides the integration layer between the MCP server and the
existing Bakufu workflow execution engine, handling the conversion between
MCP tool calls and workflow executions.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from bakufu.core.config_loader import ConfigLoader
from bakufu.core.execution_engine import WorkflowExecutionEngine
from bakufu.core.models import ExecutionContext, Workflow, WorkflowConfig
from bakufu.core.unified_input import UnifiedInputProcessor
from bakufu.core.workflow_loader import WorkflowLoader

logger = logging.getLogger(__name__)


class WorkflowExecutionResult(BaseModel):
    """Result of workflow execution for MCP responses."""

    success: bool = Field(description="Whether the workflow executed successfully")
    workflow_name: str = Field(description="Name of the executed workflow")
    result: Any = Field(description="Workflow execution result")
    error_message: str | None = Field(None, description="Error message if execution failed")
    usage_summary: dict[str, Any] | None = Field(None, description="AI usage summary")
    execution_time: float | None = Field(None, description="Execution time in seconds")


class MCPWorkflowIntegrator:
    """
    Integration layer between MCP server and Bakufu workflow engine.

    This class handles the conversion between MCP tool calls and workflow
    executions, providing a clean interface for the MCP server.
    """

    def __init__(self, workflow_dir: Path | None = None, config_path: Path | None = None):
        """
        Initialize the MCP workflow integrator.

        Args:
            workflow_dir: Directory containing workflow files
            config_path: Path to bakufu configuration file
        """
        self.workflow_dir = workflow_dir or Path("examples")
        self.config_path = config_path or Path("bakufu.yml")

        # Initialize components
        self.config_loader = ConfigLoader()
        self.workflow_loader = WorkflowLoader()
        self.input_processor = UnifiedInputProcessor()

        # Cache for loaded workflows and config
        self._workflow_cache: dict[str, Workflow] = {}
        self._config: WorkflowConfig | None = None
        self._execution_engine: WorkflowExecutionEngine | None = None

    async def initialize(self) -> None:
        """Initialize the integrator with configuration and execution engine."""
        # Load configuration
        if self.config_path.exists():
            bakufu_config = self.config_loader.load_config(self.config_path)
            self._config = WorkflowConfig.from_bakufu_config(bakufu_config)
        else:
            self._config = WorkflowConfig()
            logger.warning(f"Configuration file {self.config_path} not found, using defaults")

        # Initialize execution engine
        self._execution_engine = WorkflowExecutionEngine()

        logger.info("MCP workflow integrator initialized")

    async def discover_workflows(self) -> list[Workflow]:
        """
        Discover all available workflows in the workflow directory.

        Returns:
            List of discovered workflow definitions
        """
        workflows: list[Workflow] = []

        if not self.workflow_dir.exists():
            logger.warning(f"Workflow directory {self.workflow_dir} does not exist")
            return workflows

        # Find all YAML files
        workflow_files = list(self.workflow_dir.glob("*.yml")) + list(
            self.workflow_dir.glob("*.yaml")
        )

        for workflow_file in workflow_files:
            try:
                workflow_def = self.workflow_loader.load_from_file(workflow_file)
                workflows.append(workflow_def)

                # Cache the workflow
                self._workflow_cache[workflow_def.name] = workflow_def

                logger.debug(f"Discovered workflow: {workflow_def.name}")

            except Exception as e:
                logger.error(f"Failed to load workflow from {workflow_file}: {e}")

        logger.info(f"Discovered {len(workflows)} workflows")
        return workflows

    async def execute_workflow(
        self,
        workflow_name: str,
        input_arguments: dict[str, Any],
        mcp_context: Any = None,
        sampling_mode: bool = False,
    ) -> WorkflowExecutionResult:
        """
        Execute a workflow with the given input arguments.

        Args:
            workflow_name: Name of the workflow to execute
            input_arguments: Input arguments for the workflow
            mcp_context: MCP Context for sampling API (optional)
            sampling_mode: Whether to use MCP sampling instead of LLM providers

        Returns:
            Workflow execution result
        """
        import time

        start_time = time.time()

        try:
            # Ensure initialization
            if self._execution_engine is None:
                await self.initialize()

            # Get workflow definition
            workflow_def = await self._get_workflow_definition(workflow_name)
            if workflow_def is None:
                return WorkflowExecutionResult(
                    success=False,
                    workflow_name=workflow_name,
                    result=None,
                    error_message=f"Workflow '{workflow_name}' not found",
                    usage_summary=None,
                    execution_time=None,
                )

            # Process input arguments
            processed_inputs = self.input_processor.process_mcp_inputs(input_arguments)

            # Apply default values for missing optional parameters
            processed_inputs = self._apply_default_values(workflow_def, processed_inputs)

            # Validate input parameters
            validation_result = self._validate_workflow_inputs(workflow_def, processed_inputs)
            if not validation_result["valid"]:
                return WorkflowExecutionResult(
                    success=False,
                    workflow_name=workflow_name,
                    result=None,
                    error_message=f"Input validation failed: {validation_result['errors']}",
                    usage_summary=None,
                    execution_time=None,
                )

            # Create execution context
            assert self._config is not None
            context = ExecutionContext(
                workflow_name=workflow_name,
                input_data=processed_inputs,
                config=self._config,
                sampling_mode=sampling_mode,
                mcp_context=mcp_context,
            )

            # Execute workflow
            assert self._execution_engine is not None
            result = await self._execution_engine.execute_workflow(workflow_def, context)

            # Calculate execution time
            execution_time = time.time() - start_time

            # Get usage summary
            usage_summary = context.get_usage_summary()

            return WorkflowExecutionResult(
                success=True,
                workflow_name=workflow_name,
                result=result,
                error_message=None,
                usage_summary={
                    "total_api_calls": usage_summary.total_api_calls,
                    "total_tokens": usage_summary.total_tokens,
                    "total_cost_usd": usage_summary.total_cost_usd,
                }
                if usage_summary.total_api_calls > 0
                else None,
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Error executing workflow {workflow_name}: {e}")

            return WorkflowExecutionResult(
                success=False,
                workflow_name=workflow_name,
                result=None,
                error_message=str(e),
                usage_summary=None,
                execution_time=execution_time,
            )

    async def get_workflow_schema(self, workflow_name: str) -> dict[str, Any] | None:
        """
        Get the JSON schema for a workflow's input parameters.

        Args:
            workflow_name: Name of the workflow

        Returns:
            JSON schema dictionary or None if workflow not found
        """
        workflow_def = await self._get_workflow_definition(workflow_name)
        if workflow_def is None:
            return None

        schema: dict[str, Any] = {"type": "object", "properties": {}, "required": []}

        if workflow_def.input_parameters:
            for param_def in workflow_def.input_parameters:
                param_schema = {
                    "type": self._map_parameter_type(param_def.type),
                    "description": param_def.description or f"Input parameter: {param_def.name}",
                }

                if param_def.default is not None:
                    param_schema["default"] = param_def.default

                schema["properties"][param_def.name] = param_schema

                if param_def.required:
                    schema["required"].append(param_def.name)

        return schema

    async def _get_workflow_definition(self, workflow_name: str) -> Workflow | None:
        """
        Get workflow definition by name, loading if not cached.

        Args:
            workflow_name: Name of the workflow

        Returns:
            Workflow definition or None if not found
        """
        # Check cache first
        if workflow_name in self._workflow_cache:
            return self._workflow_cache[workflow_name]

        # Search for workflow file
        workflow_files = list(self.workflow_dir.glob(f"{workflow_name}.yml")) + list(
            self.workflow_dir.glob(f"{workflow_name}.yaml")
        )

        for workflow_file in workflow_files:
            try:
                workflow_def = self.workflow_loader.load_from_file(workflow_file)
                if workflow_def.name == workflow_name:
                    self._workflow_cache[workflow_name] = workflow_def
                    return workflow_def
            except Exception as e:
                logger.error(f"Failed to load workflow from {workflow_file}: {e}")

        # If not found by filename, search all workflows
        await self.discover_workflows()
        return self._workflow_cache.get(workflow_name)

    def _validate_workflow_inputs(
        self, workflow_def: Workflow, inputs: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Validate workflow input parameters.

        Args:
            workflow_def: Workflow definition
            inputs: Input parameters to validate

        Returns:
            Validation result with 'valid' boolean and 'errors' list
        """
        errors = []

        if not workflow_def.input_parameters:
            return {"valid": True, "errors": []}

        # Check required parameters
        for param_def in workflow_def.input_parameters:
            if param_def.required and param_def.name not in inputs and param_def.default is None:
                errors.append(f"Required parameter '{param_def.name}' is missing")

        # Validate parameter types
        param_dict = {p.name: p for p in workflow_def.input_parameters}
        for param_name, value in inputs.items():
            if param_name in param_dict:
                param_def = param_dict[param_name]
                if not self._validate_parameter_type(value, param_def.type):
                    errors.append(
                        f"Parameter '{param_name}' expected type '{param_def.type}' "
                        f"but got '{type(value).__name__}'"
                    )

        return {"valid": len(errors) == 0, "errors": errors}

    def _apply_default_values(
        self, workflow_def: Workflow, inputs: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Apply default values for missing optional parameters.

        Args:
            workflow_def: Workflow definition
            inputs: Input parameters

        Returns:
            Input parameters with default values applied
        """
        processed_inputs = dict(inputs)  # Copy the inputs

        if workflow_def.input_parameters:
            for param_def in workflow_def.input_parameters:
                if param_def.name not in processed_inputs and param_def.default is not None:
                    processed_inputs[param_def.name] = param_def.default

        return processed_inputs

    def _validate_parameter_type(self, value: Any, expected_type: str) -> bool:
        """
        Validate that a value matches the expected parameter type.

        Args:
            value: Value to validate
            expected_type: Expected type name

        Returns:
            True if valid, False otherwise
        """
        if value is None:
            return True  # None is allowed for optional parameters

        type_validators = {
            "string": lambda v: isinstance(v, str),
            "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
            "float": lambda v: isinstance(v, int | float) and not isinstance(v, bool),
            "boolean": lambda v: isinstance(v, bool),
            "array": lambda v: isinstance(v, list),
            "object": lambda v: isinstance(v, dict),
        }

        validator = type_validators.get(expected_type)
        return validator(value) if validator else True

    def _map_parameter_type(self, param_type: str) -> str:
        """
        Map workflow parameter type to JSON schema type.

        Args:
            param_type: Workflow parameter type

        Returns:
            JSON schema type
        """
        type_mapping = {
            "string": "string",
            "integer": "integer",
            "float": "number",
            "boolean": "boolean",
            "array": "array",
            "object": "object",
        }

        return type_mapping.get(param_type, "string")


class MCPProgressHandler:
    """
    Progress handler for MCP workflow executions.

    This class captures progress events from workflow execution and can
    provide real-time feedback to MCP clients if needed.
    """

    def __init__(self) -> None:
        self.current_step = 0
        self.total_steps = 0
        self.step_name = ""
        self.step_type = ""
        self.events: list[dict[str, Any]] = []

    def __call__(self, event_type: str, **kwargs: Any) -> None:
        """Handle progress events from workflow execution."""
        event = {"type": event_type, "timestamp": asyncio.get_event_loop().time(), **kwargs}

        self.events.append(event)

        if event_type == "workflow_step":
            self.current_step = kwargs.get("current_step", 0)
            self.step_name = kwargs.get("step_name", "")
            self.step_type = kwargs.get("step_type", "")

        # Log progress for debugging
        logger.debug(f"Progress event: {event_type} - {kwargs}")

    def get_progress_summary(self) -> dict[str, Any]:
        """Get current progress summary."""
        return {
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "step_name": self.step_name,
            "step_type": self.step_type,
            "total_events": len(self.events),
        }


def create_mcp_integrator(
    workflow_dir: Path | None = None, config_path: Path | None = None
) -> MCPWorkflowIntegrator:
    """
    Factory function to create an MCP workflow integrator.

    Args:
        workflow_dir: Directory containing workflow files
        config_path: Path to bakufu configuration file

    Returns:
        MCPWorkflowIntegrator instance
    """
    return MCPWorkflowIntegrator(workflow_dir=workflow_dir, config_path=config_path)
