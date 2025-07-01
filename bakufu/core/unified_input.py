"""
Unified input processing for CLI and MCP Server.

This module provides a consistent way to handle input parameters for both
CLI execution and MCP server tool calls, supporting the unified input format
specification with @file: prefixes.
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

        # 2. 各キーに@file:があるか検証。なければ警告のみ
        for key, _value in arguments.items():
            if not (isinstance(key, str) and key.startswith("@file:")):
                logger.warning(f"MCP input key '{key}' should start with '@file:' (spec violation)")

        return self.process_unified_inputs(arguments)

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
        # Handle Windows absolute paths by checking for drive letters
        file_path, file_format, encoding = self._parse_file_spec(file_spec)

        # Use existing file processor logic
        file_input_spec = f"temp={file_path}:{file_format}:{encoding}"
        processed = self.file_processor.process_file_inputs((file_input_spec,))

        return processed.get("temp") if processed else None

    def _parse_file_spec(self, file_spec: str) -> tuple[str, str, str]:
        """
        Parse file specification handling Windows absolute paths.

        Args:
            file_spec: File specification (path:format:encoding)

        Returns:
            Tuple of (file_path, file_format, encoding)
        """
        import re

        # Check if this looks like a Windows absolute path (C:, D:, etc.)
        windows_drive_pattern = r"^[A-Za-z]:[/\\]"
        if re.match(windows_drive_pattern, file_spec):
            return self._parse_windows_file_spec(file_spec)
        else:
            return self._parse_unix_file_spec(file_spec)

    def _parse_windows_file_spec(self, file_spec: str) -> tuple[str, str, str]:
        """Parse Windows absolute path file specification."""
        import re

        known_formats = {"text", "json", "yaml", "yml", "csv", "tsv", "lines"}
        common_encodings = {"utf-8", "utf-16", "ascii", "latin-1", "cp1252", "shift_jis", "euc-jp"}

        # Extract drive letter part (e.g., "C:" or "C:\")
        drive_match = re.match(r"^[A-Za-z]:[/\\]?", file_spec)
        drive_part = drive_match.group(0) if drive_match else ""
        remaining_spec = file_spec[len(drive_part) :]

        if ":" not in remaining_spec:
            return file_spec, "text", "utf-8"

        return self._parse_windows_spec_with_colons(
            file_spec, drive_part, remaining_spec, known_formats, common_encodings
        )

    def _parse_windows_spec_with_colons(
        self,
        file_spec: str,
        drive_part: str,
        remaining_spec: str,
        known_formats: set[str],
        common_encodings: set[str],
    ) -> tuple[str, str, str]:
        """Parse Windows file spec that contains colons."""
        MAX_SPLITS = 2
        PARTS_WITH_FORMAT = 2
        PARTS_WITH_FORMAT_AND_ENCODING = 3

        parts = remaining_spec.rsplit(":", MAX_SPLITS)

        if len(parts) == 1:
            return file_spec, "text", "utf-8"
        elif len(parts) == PARTS_WITH_FORMAT:
            return self._handle_windows_two_parts(file_spec, drive_part, parts, known_formats)
        elif len(parts) == PARTS_WITH_FORMAT_AND_ENCODING:
            return self._handle_windows_three_parts(
                file_spec, drive_part, parts, known_formats, common_encodings
            )
        else:
            return file_spec, "text", "utf-8"

    def _handle_windows_two_parts(
        self, file_spec: str, drive_part: str, parts: list[str], known_formats: set[str]
    ) -> tuple[str, str, str]:
        """Handle Windows file spec with two parts (path:format)."""
        potential_format = parts[1]
        if potential_format.lower() in known_formats:
            return drive_part + parts[0], potential_format, "utf-8"
        else:
            return file_spec, "text", "utf-8"

    def _handle_windows_three_parts(
        self,
        file_spec: str,
        drive_part: str,
        parts: list[str],
        known_formats: set[str],
        common_encodings: set[str],
    ) -> tuple[str, str, str]:
        """Handle Windows file spec with three parts (path:format:encoding)."""
        potential_format = parts[1]
        potential_encoding = parts[2]

        if (
            potential_format.lower() in known_formats
            and potential_encoding.lower() in common_encodings
        ) or potential_format.lower() in known_formats:
            return drive_part + parts[0], potential_format, potential_encoding
        else:
            return file_spec, "text", "utf-8"

    def _parse_unix_file_spec(self, file_spec: str) -> tuple[str, str, str]:
        """Parse Unix-style or relative path file specification."""
        MAX_SPLITS = 2
        MIN_PARTS_FOR_ENCODING = 3
        parts = file_spec.split(":", MAX_SPLITS)
        file_path = parts[0]
        file_format = parts[1] if len(parts) > 1 else "text"
        encoding = parts[2] if len(parts) >= MIN_PARTS_FOR_ENCODING else "utf-8"
        return file_path, file_format, encoding

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
            unified_inputs["_json_data"] = input_data

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
            if isinstance(key, str) and key.startswith("@"):
                try:
                    # Validate key prefix format
                    if key.startswith("@file:"):
                        self._process_file_prefix(str(value))
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
            suggestions.append(f"--input data={input_data}")

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
