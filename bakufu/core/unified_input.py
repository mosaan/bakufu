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
from ..core.models.base import StructuredInputValue


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

    def process_structured_inputs(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Process MCP tool call arguments using the structured input format.

        Only supports the structured format:
        {"param": {"type": "value/file", "data": "..."}}

        Args:
            arguments: MCP tool call arguments

        Returns:
            Dictionary of processed input parameters
        """
        import logging

        logger = logging.getLogger(__name__)

        if not isinstance(arguments, dict):
            raise ValueError(f"MCP input must be a JSON object (dict). Got: {type(arguments)}")

        processed_inputs = {}

        for key, value in arguments.items():
            # Only support structured format
            if isinstance(value, dict) and "type" in value and "data" in value:
                try:
                    structured_value = StructuredInputValue.model_validate(value)
                    if structured_value.type == "file":
                        # Process file input
                        processed_inputs[key] = self._process_structured_file_input(
                            structured_value.data,
                            structured_value.format or "text",
                            structured_value.encoding or "utf-8",
                        )
                    else:
                        # Direct value
                        processed_inputs[key] = structured_value.data
                except Exception as e:
                    logger.error(f"Invalid structured input for '{key}': {e}")
                    raise ValueError(f"Invalid structured input for '{key}': {e}") from e
            else:
                # Reject non-structured input
                raise ValueError(
                    f"Parameter '{key}' must use structured format: "
                    '{"type": "value/file", "data": "..."}'
                )

        logger.debug("Structured input format processed successfully")
        return processed_inputs

    def _process_structured_file_input(
        self, file_path: str, file_format: str, encoding: str
    ) -> Any:
        """
        Process a structured file input.

        Args:
            file_path: Path to the file
            file_format: File format (text, json, yaml, csv, lines)
            encoding: File encoding

        Returns:
            Processed file content
        """
        # Use existing file processor logic
        file_input_spec = f"temp={file_path}:{file_format}:{encoding}"
        processed = self.file_processor.process_file_inputs((file_input_spec,))

        return processed.get("temp") if processed else None


def create_unified_processor() -> UnifiedInputProcessor:
    """Factory function to create a unified input processor."""
    return UnifiedInputProcessor()
