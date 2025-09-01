"""bakufu CLI module"""

import json
import sys
from typing import Any, TypedDict, Unpack

import click
from pydantic import BaseModel
from rich.console import Console

from .core.config_loader import ConfigLoader
from .core.exceptions import BakufuError, ErrorReporter
from .core.execution_engine import WorkflowExecutionEngine
from .core.models import ExecutionContext, InputParameter, Workflow, WorkflowConfig
from .core.progress import ProgressManager
from .core.workflow_loader import WorkflowLoader

console = Console()


class RunCommandKwargs(TypedDict, total=False):
    """Type definition for run command kwargs from click"""

    workflow_file: str
    provider: str | None
    input_data: str | None
    input_file: str | None
    file_inputs: tuple[str, ...]
    output: str | None
    output_format: str
    verbose: bool
    dry_run: bool


class RunCommandOptions(BaseModel):
    """Options for the 'run' command"""

    workflow_file: str
    provider: str | None = None
    input_data: str | None = None
    input_file: str | None = None
    file_inputs: tuple[str, ...]
    output: str | None = None
    output_format: str
    verbose: bool
    dry_run: bool


# Type aliases for better type safety
InputData = dict[str, Any]  # Input data dictionary
WorkflowOutput = dict[str, Any] | str  # Workflow output can be dict or string


@click.group()
@click.version_option()
@click.option("--config", type=click.Path(), help="Config file path")
@click.pass_context
def cli(ctx: click.Context, config: str) -> None:
    """bakufu - AI Workflow CLI Tool"""
    ctx.ensure_object(dict)
    ctx.obj["config"] = config


@cli.command()
@click.argument("workflow_file", type=click.Path(exists=True))
@click.option("--provider", help="AI provider")
@click.option("--input", "input_data", help="Input parameters (JSON)")
@click.option("--input-file", type=click.Path(exists=True), help="Input file (JSON)")
@click.option(
    "--input-file-for",
    "file_inputs",
    multiple=True,
    help="File input in format key=path[:format[:encoding]] (can be used multiple times, e.g., --input-file-for content=./file.txt)",
)
@click.option("--output", type=click.Path(), help="Output file")
@click.option(
    "--output-format",
    type=click.Choice(["text", "json", "yaml"]),
    default="text",
    help="Output format",
)
@click.option("--verbose", is_flag=True, help="Verbose output")
@click.option("--dry-run", is_flag=True, help="Validate only, don't execute")
@click.pass_context
def run(ctx: click.Context, **kwargs: Unpack[RunCommandKwargs]) -> None:
    """Execute a workflow"""
    options = RunCommandOptions(**kwargs)
    try:
        workflow = _load_and_display_workflow(options.workflow_file, options.verbose)
        input_dict = _parse_input_data(options.input_data, options.input_file, options.file_inputs)

        # Validate and apply default values for input parameters
        validated_input_dict = _validate_and_apply_defaults(workflow, input_dict)

        if options.verbose and validated_input_dict:
            console.print(
                f"📥 Input data: {json.dumps(validated_input_dict, indent=2, ensure_ascii=False)}"
            )

        if options.dry_run:
            _handle_dry_run()
            return

        results, execution_context = _execute_workflow(
            workflow,
            validated_input_dict,
            options.provider,
            ctx.obj.get("config"),
            options.output_format,
        )
        _handle_output(
            results,
            workflow,
            options.output_format,
            options.output,
            options.verbose,
            validated_input_dict,
        )
        _display_usage_summary(execution_context)

    except BakufuError as e:
        _handle_bakufu_error(ctx, e, options.verbose)
    except Exception as e:
        _handle_unexpected_error(ctx, e, options.verbose)


# CLI Helper Functions
def _parse_input_data(
    input_data: str | None, input_file: str | None, file_inputs: tuple[str, ...] | None = None
) -> InputData:
    """Parse input data from various sources"""
    input_dict = {}

    if input_file:
        with open(input_file) as f:
            input_dict = json.load(f)
    elif input_data:
        input_dict = json.loads(input_data)
    elif not sys.stdin.isatty():
        # Read from stdin if available
        stdin_data = sys.stdin.read().strip()
        if stdin_data:
            try:
                input_dict = json.loads(stdin_data)
            except json.JSONDecodeError:
                input_dict = {"text": stdin_data}

    # Process file inputs
    if file_inputs:
        from .core.input_processor import FileInputProcessor

        processor = FileInputProcessor()
        file_data = processor.process_file_inputs(file_inputs)
        if file_data:
            # Check for key conflicts and warn
            conflicts = set(input_dict.keys()) & set(file_data.keys())
            if conflicts:
                console.print(
                    f"⚠️  Warning: Key conflicts detected between --input and --input-file-for: {', '.join(conflicts)}. "
                    f"--input-file-for values will take priority.",
                    style="yellow",
                )

            # Merge file data directly into input_dict (--input-file-for takes priority)
            input_dict.update(file_data)

    return input_dict


def _create_execution_context(
    workflow: Workflow,
    input_dict: InputData,
    provider: str | None,
    config_path: str | None = None,
) -> ExecutionContext:
    """Create execution context with configuration"""
    try:
        # Load configuration from bakufu.yml files
        from pathlib import Path

        bakufu_config = ConfigLoader.load_config(Path(config_path) if config_path else None)
        config = WorkflowConfig.from_bakufu_config(bakufu_config)
    except Exception:
        # Fall back to default configuration if loading fails
        config = WorkflowConfig()

    if provider:
        config.default_provider = provider

    return ExecutionContext(workflow_name=workflow.name, input_data=input_dict, config=config)


def _format_output(
    results: WorkflowOutput,
    output_format: str,
    workflow: Workflow,
    input_data: InputData | None = None,
) -> str:
    """Format workflow execution results"""
    if output_format == "json":
        return json.dumps(results, indent=2, ensure_ascii=False)
    elif output_format == "yaml":
        import yaml

        return yaml.dump(results, default_flow_style=False, allow_unicode=True)
    elif workflow.output and workflow.output.template and isinstance(results, dict):
        from .core.template_engine import WorkflowTemplateEngine

        engine = WorkflowTemplateEngine()
        context = {"steps": results, "input": input_data or {}}
        return engine.render(workflow.output.template, context)
    elif isinstance(results, dict) and len(results) == 1:
        return str(next(iter(results.values())))
    elif isinstance(results, str):
        return results
    else:
        return json.dumps(results, indent=2, ensure_ascii=False)


def _save_output(content: str, output_path: str) -> None:
    """Save output to file"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


def _load_and_display_workflow(workflow_file: str, verbose: bool) -> Workflow:
    """Load workflow and display information if verbose"""
    if verbose:
        console.print(f"🚀 Running workflow: {workflow_file}")

    workflow = WorkflowLoader.load_from_file(workflow_file)

    if verbose:
        console.print(f"📋 Loaded workflow: {workflow.name}")
        console.print(f"📊 Steps: {len(workflow.steps)}")

    return workflow


def _display_usage_summary(context: "ExecutionContext") -> None:
    """Display usage summary for the workflow execution"""
    usage = context.get_usage_summary()

    if usage.total_api_calls == 0:
        return  # No AI calls were made

    console.print("\n📊 AI Usage Summary:")
    console.print(f"  🔄 Total API calls: {usage.total_api_calls}")
    console.print(
        f"  📝 Total tokens: {usage.total_tokens:,} ({usage.total_prompt_tokens:,} prompt + {usage.total_completion_tokens:,} completion)"
    )
    console.print(f"  💰 Total cost: ${usage.total_cost_usd:.6f} USD")


def _handle_dry_run() -> None:
    """Handle dry run mode output"""
    console.print("✅ Workflow validation successful")
    console.print("🏃 Dry run mode - execution skipped")


def _execute_workflow(
    workflow: Workflow,
    input_dict: InputData,
    provider: str | None,
    config_path: str | None = None,
    output_format: str = "text",
) -> tuple[WorkflowOutput, "ExecutionContext"]:
    """Execute workflow and return results with context"""
    context = _create_execution_context(workflow, input_dict, provider, config_path)

    # Create progress manager (suppress output for structured formats)
    should_show_progress = output_format == "text"
    progress_manager = ProgressManager(console) if should_show_progress else None

    # Create progress callback function
    def progress_callback(event_type: str, **kwargs: Any) -> None:
        """Handle progress events from execution engine"""
        if not progress_manager:
            return

        if event_type == "workflow_step":
            progress_manager.update_workflow_step(
                kwargs["current_step"], kwargs["step_name"], kwargs["step_type"]
            )

    # Create engine with progress callback
    engine = WorkflowExecutionEngine(progress_callback=progress_callback)

    import asyncio

    # Use workflow progress context manager
    if progress_manager:
        with progress_manager.workflow_progress(workflow.name, len(workflow.steps)):
            results = asyncio.run(engine.execute_workflow(workflow, context))
    else:
        results = asyncio.run(engine.execute_workflow(workflow, context))

    return results, context


def _handle_output(  # noqa: PLR0913
    results: WorkflowOutput,
    workflow: Workflow,
    output_format: str,
    output: str | None,
    verbose: bool,
    input_data: InputData | None = None,
) -> None:
    """Handle workflow output formatting and saving"""
    # Format output
    final_output: dict[str, Any] | str
    if workflow.output and workflow.output.template:
        from .core.execution_engine import ExecutionContext
        from .core.models import WorkflowConfig

        # Create a temporary context for template rendering
        config = WorkflowConfig()
        context = ExecutionContext(
            workflow_name=workflow.name, input_data=input_data or {}, config=config
        )
        # Update context with results for template rendering
        context.step_outputs = results  # type: ignore[assignment]
        final_output = context.render_template(workflow.output.template)
    else:
        final_output = results

    # Handle output formatting
    if workflow.output and workflow.output.template:
        # Template was already processed, just format the output
        if output_format == "json":
            formatted_output = json.dumps(
                {"result": final_output, "steps": results}, indent=2, ensure_ascii=False
            )
        elif output_format == "yaml":
            import yaml

            formatted_output = yaml.dump(
                {"result": final_output, "steps": results},
                default_flow_style=False,
                allow_unicode=True,
            )
        else:
            formatted_output = str(final_output)
    else:
        formatted_output = _format_output(final_output, output_format, workflow, input_data or {})

    # Output results
    if output:
        _save_output(formatted_output, output)
        if verbose:
            console.print(f"💾 Output written to: {output}")
    else:
        console.print(formatted_output)


def _handle_bakufu_error(ctx: click.Context, error: BakufuError, verbose: bool) -> None:
    """Handle BakufuError exceptions"""
    error_msg = ErrorReporter.format_error_for_cli(error, verbose=verbose)
    console.print(error_msg, style="bold red")
    ctx.exit(1)


def _handle_unexpected_error(ctx: click.Context, error: Exception, verbose: bool) -> None:
    """Handle unexpected exceptions"""
    if verbose:
        console.print_exception()
    else:
        console.print(f"❌ Unexpected error: {error}", style="bold red")
    ctx.exit(1)


def _load_and_validate_workflow(workflow_file: str, verbose: bool) -> Workflow:
    """Load and validate workflow with optional verbose output"""
    if verbose:
        console.print(f"🔍 Validating workflow: {workflow_file}")

    workflow = WorkflowLoader.load_from_file(workflow_file)

    if verbose:
        console.print(f"📋 Workflow: {workflow.name}")
        console.print(f"📝 Description: {workflow.description or 'None'}")
        console.print(f"📊 Steps: {len(workflow.steps)}")
        console.print(f"🔢 Input parameters: {len(workflow.input_parameters or [])}")

    return workflow


def _validate_and_apply_defaults(workflow: Workflow, input_dict: InputData) -> InputData:
    """Validate input parameters and apply default values"""
    if not workflow.input_parameters:
        return input_dict

    validated_input = input_dict.copy()

    for param in workflow.input_parameters:
        param_name = param.name

        # Check if parameter is provided
        if param_name not in validated_input:
            if param.required and param.default is None:
                raise BakufuError(
                    f"Required parameter '{param_name}' is missing", "MISSING_REQUIRED_PARAMETER"
                )
            elif param.default is not None:
                validated_input[param_name] = param.default
                continue

        # Validate parameter type if value is provided
        if param_name in validated_input:
            value = validated_input[param_name]
            if not _validate_parameter_type(value, param):
                expected_type = param.type
                actual_type = type(value).__name__
                raise BakufuError(
                    f"Parameter '{param_name}' expected type '{expected_type}' but got '{actual_type}'",
                    "INVALID_PARAMETER_TYPE",
                )

    return validated_input


def _validate_parameter_type(value: Any, param: InputParameter) -> bool:
    """Validate that a value matches the expected parameter type"""
    if value is None:
        return not param.required or param.default is not None

    type_validators = {
        "string": lambda v: isinstance(v, str),
        "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
        "float": lambda v: isinstance(v, int | float) and not isinstance(v, bool),
        "boolean": lambda v: isinstance(v, bool),
        "array": lambda v: type(v).__name__ == "list",
        "object": lambda v: type(v).__name__ == "dict",
    }

    validator = type_validators.get(param.type)
    return validator(value) if validator else True


def _create_dummy_input(workflow: Workflow) -> InputData:
    """Create dummy input data for template validation"""
    dummy_input = {}

    if workflow.input_parameters:
        for param in workflow.input_parameters:
            if param.default is not None:
                dummy_input[param.name] = param.default
            elif param.type == "string":
                dummy_input[param.name] = "test"
            elif param.type == "integer":
                dummy_input[param.name] = 42
            elif param.type == "float":
                dummy_input[param.name] = 3.14
            elif param.type == "boolean":
                dummy_input[param.name] = True
            elif param.type == "array":
                dummy_input[param.name] = []
            elif param.type == "object":
                dummy_input[param.name] = {}

    return dummy_input


def _validate_step_templates(
    workflow: Workflow, context: ExecutionContext, verbose: bool, ctx: click.Context
) -> None:
    """Validate templates in workflow steps"""
    for step in workflow.steps:
        if hasattr(step, "prompt"):
            # AI call step
            try:
                context.validate_template(step.prompt)
                if verbose:
                    console.print(f"  ✅ Step '{step.id}' prompt template valid")
            except Exception as e:
                console.print(f"  ❌ Step '{step.id}' prompt template error: {e}", style="red")
                ctx.exit(1)
        elif hasattr(step, "input"):
            # Text process step
            try:
                context.validate_template(step.input)
                if verbose:
                    console.print(f"  ✅ Step '{step.id}' input template valid")
            except Exception as e:
                console.print(f"  ❌ Step '{step.id}' input template error: {e}", style="red")
                ctx.exit(1)


def _validate_output_template(
    workflow: Workflow, context: ExecutionContext, verbose: bool, ctx: click.Context
) -> None:
    """Validate output template if present"""
    if workflow.output and workflow.output.template:
        try:
            context.validate_template(workflow.output.template)
            if verbose:
                console.print("  ✅ Output template valid")
        except Exception as e:
            console.print(f"  ❌ Output template error: {e}", style="red")
            ctx.exit(1)


def _perform_extended_validation(
    workflow: Workflow, template_check: bool, verbose: bool, ctx: click.Context
) -> None:
    """Perform extended validation beyond schema checking"""
    # Create dummy context for template validation
    config = WorkflowConfig()
    dummy_input = _create_dummy_input(workflow)

    context = ExecutionContext(workflow_name=workflow.name, input_data=dummy_input, config=config)

    # Validate templates if requested
    if template_check:
        if verbose:
            console.print("🎨 Checking template syntax...")

        _validate_step_templates(workflow, context, verbose, ctx)
        _validate_output_template(workflow, context, verbose, ctx)


@cli.group()
def config() -> None:
    """Configuration management"""
    pass


@config.command()
@click.option("--path", type=click.Path(), help="Configuration file path")
@click.option("--global", "global_config", is_flag=True, help="Create global configuration")
def init(path: str | None, global_config: bool) -> None:
    """Initialize configuration"""
    from pathlib import Path

    console.print("⚙️ Initializing configuration...")

    if path:
        config_path = Path(path)
    elif global_config:
        config_path = Path.home() / ".config" / "bakufu" / "config.yml"
    else:
        config_path = Path.cwd() / "bakufu.yml"

    if config_path.exists():
        console.print(f"⚠️ Configuration file already exists: {config_path}")
        if not click.confirm("Overwrite existing configuration?"):
            return

    try:
        ConfigLoader.create_default_config(config_path)
        console.print(f"✅ Configuration initialized: {config_path}")
        console.print("📝 Please edit the configuration file to set your API keys")
    except Exception as e:
        console.print(f"❌ Failed to create configuration: {e}", style="red")


@config.command()
@click.option("--path", type=click.Path(), help="Configuration file path")
def list(path: str | None) -> None:
    """List current configuration"""
    import json
    from pathlib import Path

    console.print("📋 Current configuration:")

    try:
        bakufu_config = ConfigLoader.load_config(Path(path) if path else None)

        # Display configuration files found
        config_files = ConfigLoader.find_config_files()
        if config_files:
            console.print("📁 Configuration files found:")
            for config_file in config_files:
                console.print(f"  - {config_file}")
        else:
            console.print("📁 No configuration files found (using defaults)")

        console.print("\n⚙️ Current settings:")
        config_dict = bakufu_config.model_dump()

        # Hide sensitive information
        if "provider_settings" in config_dict:
            for _provider, settings in config_dict["provider_settings"].items():
                if isinstance(settings, dict) and "api_key" in settings and settings["api_key"]:
                    settings["api_key"] = "***"

        console.print(json.dumps(config_dict, indent=2, ensure_ascii=False))

    except Exception as e:
        console.print(f"❌ Failed to load configuration: {e}", style="red")


@cli.command()
@click.argument("workflow_file", type=click.Path(exists=True))
@click.option("--verbose", is_flag=True, help="Verbose validation output")
@click.option("--schema-only", is_flag=True, help="Schema validation only")
@click.option("--template-check", is_flag=True, help="Template syntax check")
@click.pass_context
def validate(
    ctx: click.Context, workflow_file: str, verbose: bool, schema_only: bool, template_check: bool
) -> None:
    """Validate a workflow file"""
    try:
        workflow = _load_and_validate_workflow(workflow_file, verbose)

        if not schema_only:
            _perform_extended_validation(workflow, template_check, verbose, ctx)

        console.print("✅ Workflow validation successful", style="bold green")

        if verbose:
            console.print(f"🎯 Ready for execution with {len(workflow.steps)} steps")

    except BakufuError as e:
        _handle_bakufu_error(ctx, e, verbose)
    except Exception as e:
        _handle_unexpected_error(ctx, e, verbose)


def main() -> None:
    """Entry point for CLI"""
    cli()
