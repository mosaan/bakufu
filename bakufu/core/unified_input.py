"""
Unified input processing for CLI and MCP Server.

This module provides a consistent way to handle input parameters for both
CLI execution and MCP server tool calls, supporting the unified input format
specification with @value: and @file: prefixes.
"""

import json
import sys
from typing import Any

from ..core.input_processor import FileInputProcessor


class UnifiedInputProcessor:
    """
    Unified input processor for CLI and MCP compatibility.

    Supports the unified input format:
    - Direct values: key=value
    - File inputs: key=@file:path:format:encoding
    - JSON values: key=@value:{"key": "value"}
    """

    def __init__(self) -> None:
        self.file_processor = FileInputProcessor()

    def process_cli_inputs(
        self,
        input_data: str | None = None,
        input_file: str | None = None,
        file_inputs: tuple[str, ...] | None = None,
    ) -> dict[str, Any]:
        """
        Process CLI input arguments using current CLI format.

        Args:
            input_data: JSON string input (--input)
            input_file: JSON file path (--input-file)
            file_inputs: File input specifications (--input-file-for)

        Returns:
            Dictionary of processed input parameters
        """
        input_dict = {}

        # Handle JSON input file
        if input_file:
            with open(input_file) as f:
                input_dict = json.load(f)

        # Handle JSON string input
        elif input_data:
            input_dict = json.loads(input_data)

        # Handle stdin input
        elif not sys.stdin.isatty():
            stdin_data = sys.stdin.read().strip()
            if stdin_data:
                try:
                    input_dict = json.loads(stdin_data)
                except json.JSONDecodeError:
                    input_dict = {"text": stdin_data}

        # Process file inputs using existing processor
        if file_inputs:
            file_data = self.file_processor.process_file_inputs(file_inputs)
            if file_data:
                # Merge file data (file inputs take priority)
                input_dict.update(file_data)

        return input_dict

    def process_unified_inputs(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """
        Process inputs using unified format specification.

        Supports:
        - key: value  (通常値)
        - @file:key: value  (ファイル指定)
        - @value:key: value (JSON値指定)
        - key: @file:...  (従来値プレフィックス)
        - key: @value:... (従来値プレフィックス)

        Args:
            inputs: Raw input dictionary with potential prefixed keys or values

        Returns:
            Dictionary of processed input parameters
        """
        processed_inputs = {}

        for key, value in inputs.items():
            if isinstance(key, str):
                if key.startswith("@file:"):
                    real_key = key[len("@file:") :]
                    processed_inputs[real_key] = self._process_file_prefix(value)
                elif key.startswith("@value:"):
                    real_key = key[len("@value:") :]
                    processed_inputs[real_key] = self._process_value_prefix(value)
                elif isinstance(value, str) and value.startswith("@file:"):
                    processed_inputs[key] = self._process_file_prefix(value[6:])
                elif isinstance(value, str) and value.startswith("@value:"):
                    processed_inputs[key] = self._process_value_prefix(value[7:])
                else:
                    processed_inputs[key] = value
            else:
                processed_inputs[key] = value

        return processed_inputs

    def process_mcp_inputs(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Process MCP tool call arguments.

        MCP arguments are already processed by the client, but this method
        provides a consistent interface and handles any special processing
        that might be needed for MCP-specific scenarios.

        Args:
            arguments: MCP tool call arguments

        Returns:
            Dictionary of processed input parameters
        """
        import logging

        logger = logging.getLogger(__name__)
        # 1. 入力がdict型でなければ例外
        if not isinstance(arguments, dict):
            raise ValueError(f"MCP input must be a JSON object (dict). Got: {type(arguments)}")

        # 2. 各キーまたは値に@value:や@file:があるか検証。なければ警告のみ
        for key, value in arguments.items():
            if not (
                (isinstance(key, str) and (key.startswith("@value:") or key.startswith("@file:")))
                or (
                    isinstance(value, str)
                    and (value.startswith("@value:") or value.startswith("@file:"))
                )
            ):
                logger.warning(
                    f"MCP input key '{key}' should start with '@value:' or '@file:', or its value should start with '@value:' or '@file:' (spec violation)"
                )

        return self.process_unified_inputs(arguments)

    def _process_prefixed_value(self, value: str) -> Any:
        """
        Process a prefixed value (@file:, @value:, etc.).

        Args:
            value: Prefixed value string

        Returns:
            Processed value
        """
        if value.startswith("@file:"):
            return self._process_file_prefix(value[6:])  # Remove "@file:" prefix
        elif value.startswith("@value:"):
            return self._process_value_prefix(value[7:])  # Remove "@value:" prefix
        else:
            # Unknown prefix, return as-is
            return value

    def _process_file_prefix(self, file_spec: str) -> Any:
        """
        Process @file: prefixed value.

        Format: path:format:encoding
        Where format and encoding are optional.

        Args:
            file_spec: File specification (path:format:encoding)

        Returns:
            Processed file content
        """
        MAX_PARTS = 3
        ENCODING_INDEX = 2
        parts = file_spec.split(":", MAX_PARTS - 1)
        file_path = parts[0]
        file_format = parts[1] if len(parts) > 1 else "text"
        encoding = parts[ENCODING_INDEX] if len(parts) > ENCODING_INDEX else "utf-8"

        # Use existing file processor logic
        file_input_spec = f"temp={file_path}:{file_format}:{encoding}"
        processed = self.file_processor.process_file_inputs((file_input_spec,))

        return processed.get("temp") if processed else None

    def _process_value_prefix(self, value_string: str) -> Any:
        """
        Process @value: prefixed value.

        Args:
            value_string: JSON string to parse

        Returns:
            Parsed JSON value
        """
        try:
            return json.loads(value_string)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in @value: prefix: {e}") from e

    def convert_cli_to_unified_format(
        self,
        input_data: str | None = None,
        input_file: str | None = None,
        file_inputs: tuple[str, ...] | None = None,
    ) -> dict[str, str]:
        """
        Convert current CLI input format to unified format.

        This is useful for migration and testing purposes.

        Args:
            input_data: JSON string input
            input_file: JSON file path
            file_inputs: File input specifications

        Returns:
            Dictionary with unified format values
        """
        unified_inputs = {}

        # Convert JSON file input
        if input_file:
            unified_inputs["_json_file"] = f"@file:{input_file}:json"

        # Convert JSON string input
        if input_data:
            unified_inputs["_json_data"] = f"@value:{input_data}"

        # Convert file inputs
        if file_inputs:
            for file_input in file_inputs:
                if "=" in file_input:
                    key, file_spec = file_input.split("=", 1)
                    unified_inputs[key] = f"@file:{file_spec}"

        return unified_inputs

    def validate_unified_format(self, inputs: dict[str, Any]) -> dict[str, str]:
        """
        Validate unified format inputs and return any errors.

        Args:
            inputs: Input dictionary to validate

        Returns:
            Dictionary of validation errors (empty if valid)
        """
        errors = {}

        for key, value in inputs.items():
            if isinstance(value, str) and value.startswith("@"):
                try:
                    self._process_prefixed_value(value)
                except Exception as e:
                    errors[key] = str(e)

        return errors


class CLIInputMigrator:
    """
    Helper class for migrating CLI input handling to unified format.

    This class provides utilities for gradually migrating the existing CLI
    to use the unified input format while maintaining backward compatibility.
    """

    def __init__(self) -> None:
        self.processor = UnifiedInputProcessor()

    def migrate_cli_inputs(
        self,
        input_data: str | None = None,
        input_file: str | None = None,
        file_inputs: tuple[str, ...] | None = None,
        unified_inputs: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Migrate CLI inputs with support for both old and new formats.

        Args:
            input_data: Legacy JSON string input
            input_file: Legacy JSON file input
            file_inputs: Legacy file input specifications
            unified_inputs: New unified format inputs

        Returns:
            Processed input dictionary
        """
        # If unified inputs are provided, use them
        if unified_inputs:
            return self.processor.process_unified_inputs(unified_inputs)

        # Otherwise, use legacy format
        return self.processor.process_cli_inputs(input_data, input_file, file_inputs)

    def suggest_unified_format(
        self,
        input_data: str | None = None,
        input_file: str | None = None,
        file_inputs: tuple[str, ...] | None = None,
    ) -> str:
        """
        Suggest unified format equivalent for current CLI usage.

        Args:
            input_data: Current JSON string input
            input_file: Current JSON file input
            file_inputs: Current file input specifications

        Returns:
            Suggestion text for unified format usage
        """
        suggestions = []

        if input_file:
            suggestions.append(f"--input data=@file:{input_file}:json")

        if input_data:
            suggestions.append(f"--input data=@value:{input_data}")

        if file_inputs:
            for file_input in file_inputs:
                suggestions.append(f"--input {file_input.replace('=', '=@file:')}")

        if suggestions:
            return "Unified format equivalent:\n" + "\n".join(f"  {s}" for s in suggestions)
        else:
            return "No specific unified format suggestions for current input."


def create_unified_processor() -> UnifiedInputProcessor:
    """Factory function to create a unified input processor."""
    return UnifiedInputProcessor()


def create_cli_migrator() -> CLIInputMigrator:
    """Factory function to create a CLI input migrator."""
    return CLIInputMigrator()
