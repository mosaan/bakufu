"""YAML parsing text processing step"""

from typing import Any, Literal

import yaml

from ..exceptions import ErrorContext, StepExecutionError
from ..step_registry import step_type
from .base import TextProcessStep


@step_type("text_process", "yaml_parse")
class YamlParseStep(TextProcessStep):
    """YAML parsing text processing step"""

    method: Literal["yaml_parse"] = "yaml_parse"

    async def process(self, input_data: str, step_id: str) -> Any:
        """Parse YAML from text"""
        try:
            # Use a custom loader that doesn't auto-parse dates to maintain consistency
            class NoDateLoader(yaml.SafeLoader):
                pass

            # Add a custom constructor for timestamps that returns strings
            def timestamp_constructor(loader: yaml.Loader, node: yaml.ScalarNode) -> str:
                return loader.construct_scalar(node)

            NoDateLoader.add_constructor("tag:yaml.org,2002:timestamp", timestamp_constructor)

            return yaml.load(input_data.strip(), Loader=NoDateLoader)
        except yaml.YAMLError as e:
            raise StepExecutionError(
                message=f"Invalid YAML format: {e}",
                step_id=step_id,
                context=ErrorContext(step_id=step_id, function_name="YamlParseStep.process"),
                original_error=e,
                suggestions=[
                    "Check YAML syntax and indentation",
                    "Verify YAML structure is valid",
                    "Ensure proper key-value formatting",
                    f"Text preview: {input_data.strip()[:100]}...",
                ],
            ) from e
