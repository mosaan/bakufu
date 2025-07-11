"""File input processing module for bakufu"""

import csv
import json
import os
from pathlib import Path
from typing import Any

import yaml

from .exceptions import BakufuError


class FileInputProcessor:
    """Processes file inputs for workflow execution"""

    # Default file size limit: 10MB
    DEFAULT_MAX_FILE_SIZE = 10 * 1024 * 1024

    # Constants for parsing
    EXPECTED_PARTS_COUNT = 2
    MIN_PATH_PARTS_FOR_FORMAT = 2
    MIN_PATH_PARTS_FOR_ENCODING = 3

    # Constants for binary file detection
    BINARY_DETECTION_CHUNK_SIZE = 8192
    CONTROL_CHAR_THRESHOLD = 0.05
    PRINTABLE_CHAR_MIN = 32

    def __init__(self, max_file_size: int | None = None):
        """Initialize the file input processor"""
        self.max_file_size = max_file_size or self.DEFAULT_MAX_FILE_SIZE

    def process_file_inputs(self, file_inputs: tuple[str, ...]) -> dict[str, Any]:
        """Process multiple file inputs and return the combined data"""
        files_data = {}

        for file_input in file_inputs:
            key, file_data = self._process_single_file_input(file_input)
            files_data[key] = file_data

        return files_data

    def _process_single_file_input(self, file_input: str) -> tuple[str, Any]:
        """Process a single file input in format key=path[:format[:encoding]]"""
        # Parse the file input specification
        parts = file_input.split("=", 1)
        if len(parts) != self.EXPECTED_PARTS_COUNT:
            raise BakufuError(
                f"Invalid file input format: '{file_input}'. Expected 'key=path[:format[:encoding]]'",
                "INVALID_FILE_INPUT_FORMAT",
            )

        key = parts[0].strip()
        path_spec = parts[1].strip()

        # Parse path specification with optional format and encoding
        # Handle Windows absolute paths properly
        file_path, file_format, encoding = self._parse_path_spec(path_spec)

        # Validate key
        if not key:
            raise BakufuError(
                f"File input key cannot be empty in: '{file_input}'", "EMPTY_FILE_INPUT_KEY"
            )

        # Load and process the file
        file_data = self._load_file(file_path, file_format, encoding)
        return key, file_data

    def _parse_path_spec(self, path_spec: str) -> tuple[str, str, str]:
        """Parse path specification handling Windows absolute paths.

        Args:
            path_spec: Path specification (path:format:encoding)

        Returns:
            Tuple of (file_path, file_format, encoding)
        """
        import re

        # Check if this looks like a Windows absolute path (C:, D:, etc.)
        windows_drive_pattern = r"^[A-Za-z]:[/\\]"
        if re.match(windows_drive_pattern, path_spec):
            return self._parse_windows_path_spec(path_spec)
        else:
            return self._parse_unix_path_spec(path_spec)

    def _parse_windows_path_spec(self, path_spec: str) -> tuple[str, str, str]:
        """Parse Windows absolute path specification."""
        import re

        # Constants
        MAX_SPLITS = 2
        known_formats = {"text", "json", "yaml", "yml", "csv", "tsv", "lines"}

        # Extract drive letter part (e.g., "C:" or "C:\")
        drive_match = re.match(r"^[A-Za-z]:[/\\]?", path_spec)
        drive_part = drive_match.group(0) if drive_match else ""
        remaining_spec = path_spec[len(drive_part) :]

        if ":" not in remaining_spec:
            # No format/encoding specifiers - entire spec is path
            return path_spec, self._detect_format(path_spec), "utf-8"

        # Split from the right to handle colons in the path properly
        parts = remaining_spec.rsplit(":", MAX_SPLITS)
        return self._parse_windows_path_parts(path_spec, drive_part, parts, known_formats)

    def _parse_windows_path_parts(
        self,
        path_spec: str,
        drive_part: str,
        parts: list[str],
        known_formats: set[str],
    ) -> tuple[str, str, str]:
        """Parse Windows path parts to extract file path, format, and encoding."""
        # Constants for parts count
        PARTS_COUNT_NO_SPEC = 1
        PARTS_COUNT_WITH_FORMAT = 2
        PARTS_COUNT_WITH_FORMAT_AND_ENCODING = 3

        if len(parts) == PARTS_COUNT_NO_SPEC:
            # No format/encoding specified
            return path_spec, self._detect_format(path_spec), "utf-8"
        elif len(parts) == PARTS_COUNT_WITH_FORMAT:
            # One specifier: could be format
            potential_format = parts[1]
            if potential_format.lower() in known_formats:
                return drive_part + parts[0], potential_format, "utf-8"
            else:
                # Part of path
                return path_spec, self._detect_format(path_spec), "utf-8"
        elif len(parts) == PARTS_COUNT_WITH_FORMAT_AND_ENCODING:
            # Two specifiers: format:encoding
            potential_format, potential_encoding = parts[1], parts[2]
            if potential_format.lower() in known_formats:
                return drive_part + parts[0], potential_format, potential_encoding
            else:
                # Neither looks like specifiers
                return path_spec, self._detect_format(path_spec), "utf-8"
        else:
            # More than 2 splits - likely path with many colons
            return path_spec, self._detect_format(path_spec), "utf-8"

    def _parse_unix_path_spec(self, path_spec: str) -> tuple[str, str, str]:
        """Parse Unix/relative path specification."""
        MAX_SPLITS = 2
        PARTS_WITH_FORMAT = 2

        parts = path_spec.split(":", MAX_SPLITS)
        file_path = parts[0]
        file_format = parts[1] if len(parts) > 1 else self._detect_format(file_path)
        encoding = parts[PARTS_WITH_FORMAT] if len(parts) > PARTS_WITH_FORMAT else "utf-8"

        return file_path, file_format, encoding

    def _detect_format(self, file_path: str) -> str:
        """Detect file format based on file extension"""
        extension = Path(file_path).suffix.lower()

        format_map = {
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".csv": "csv",
            ".tsv": "tsv",
            ".txt": "text",
        }

        return format_map.get(extension, "text")

    def _load_file(self, file_path: str, file_format: str, encoding: str) -> Any:
        """Load a file with the specified format and encoding"""
        # Validate file path and security constraints
        self._validate_file_path(file_path)

        try:
            self._validate_file_constraints(file_path)
            return self._load_file_by_format(file_path, file_format, encoding)

        except BakufuError:
            raise
        except FileNotFoundError as e:
            raise BakufuError(f"File not found: '{file_path}'", "FILE_NOT_FOUND") from e
        except PermissionError as e:
            raise BakufuError(
                f"Permission denied accessing file: '{file_path}'", "FILE_PERMISSION_DENIED"
            ) from e
        except Exception as e:
            raise BakufuError(f"Error loading file '{file_path}': {e}", "FILE_LOAD_ERROR") from e

    def _validate_file_constraints(self, file_path: str) -> None:
        """Validate file size and binary constraints"""
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > self.max_file_size:
            raise BakufuError(
                f"File '{file_path}' size ({file_size} bytes) exceeds maximum allowed size ({self.max_file_size} bytes)",
                "FILE_SIZE_EXCEEDED",
            )

        # Check if file is text
        if not self._is_text_file(file_path):
            raise BakufuError(
                f"Binary files are not supported: '{file_path}'", "BINARY_FILE_NOT_SUPPORTED"
            )

    def _load_file_by_format(self, file_path: str, file_format: str, encoding: str) -> Any:
        """Load file content based on format"""
        format_loaders = {
            "text": self._load_text_file,
            "lines": self._load_lines_file,
            "json": self._load_json_file,
            "yaml": self._load_yaml_file,
            "csv": self._load_csv_file,
            "tsv": self._load_tsv_file,
        }

        loader = format_loaders.get(file_format)
        if not loader:
            raise BakufuError(
                f"Unsupported file format: '{file_format}'. "
                f"Supported formats: {', '.join(format_loaders.keys())}",
                "UNSUPPORTED_FILE_FORMAT",
            )

        return loader(file_path, encoding)

    def _validate_file_path(self, file_path: str) -> None:
        """Validate file path for security constraints"""
        # Convert to absolute path for validation
        abs_path = Path(file_path).resolve()

        # Check if file exists
        if not abs_path.exists():
            raise BakufuError(f"File not found: '{file_path}'", "FILE_NOT_FOUND")

        # Check if it's actually a file (not a directory)
        if not abs_path.is_file():
            raise BakufuError(f"Path is not a file: '{file_path}'", "NOT_A_FILE")

        # Additional security checks could be added here
        # For example, checking if path is within allowed directories

    def _is_text_file(self, file_path: str) -> bool:
        """Check if a file is text by attempting UTF-8 decoding with fallback strategies"""
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(self.BINARY_DETECTION_CHUNK_SIZE)
                if not chunk:
                    return True  # Empty file is considered text

            # Check for binary markers first (null bytes are strong indicators)
            if self._contains_binary_markers(chunk):
                return False

            # First, try UTF-8 decoding (most common for text files)
            try:
                chunk.decode("utf-8")
                return True
            except UnicodeDecodeError:
                pass

            # Fallback: try Latin-1 (can decode any byte sequence)
            try:
                chunk.decode("latin-1")
                # If Latin-1 succeeds, it's likely text (binary markers already checked)
                return True
            except UnicodeDecodeError:
                return False

        except Exception:
            # If we can't read the file, assume it might be binary
            return False

    def _contains_binary_markers(self, chunk: bytes) -> bool:
        """Check for common binary file markers"""
        # Null bytes are strong indicators of binary content
        if b"\x00" in chunk:
            return True

        # Check for excessive control characters (excluding common ones)
        control_chars = sum(
            1
            for byte in chunk
            if byte < self.PRINTABLE_CHAR_MIN
            and byte not in (9, 10, 13)  # tab, newline, carriage return
        )

        # If more than threshold are control characters, likely binary
        return len(chunk) > 0 and (control_chars / len(chunk)) > self.CONTROL_CHAR_THRESHOLD

    def _load_text_file(self, file_path: str, encoding: str) -> str:
        """Load a text file and return its content as a string"""
        with open(file_path, encoding=encoding) as f:
            return f.read()

    def _load_lines_file(self, file_path: str, encoding: str) -> list[str]:
        """Load a text file and return its content as a list of lines"""
        with open(file_path, encoding=encoding) as f:
            return [line.rstrip("\n\r") for line in f]

    def _load_json_file(self, file_path: str, encoding: str) -> Any:
        """Load a JSON file and return the parsed content"""
        with open(file_path, encoding=encoding) as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as e:
                raise BakufuError(
                    f"Invalid JSON in file '{file_path}': {e}", "INVALID_JSON_FORMAT"
                ) from e

    def _load_yaml_file(self, file_path: str, encoding: str) -> Any:
        """Load a YAML file and return the parsed content"""
        with open(file_path, encoding=encoding) as f:
            try:
                return yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise BakufuError(
                    f"Invalid YAML in file '{file_path}': {e}", "INVALID_YAML_FORMAT"
                ) from e

    def _load_csv_file(self, file_path: str, encoding: str) -> list[dict[str, str]]:
        """Load a CSV file and return the content as a list of dictionaries"""
        with open(file_path, encoding=encoding, newline="") as f:
            try:
                # Detect delimiter and other parameters
                sample = f.read(1024)
                f.seek(0)

                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter

                reader = csv.DictReader(f, delimiter=delimiter)
                return list(reader)
            except Exception as e:
                raise BakufuError(
                    f"Error parsing CSV file '{file_path}': {e}", "INVALID_CSV_FORMAT"
                ) from e

    def _load_tsv_file(self, file_path: str, encoding: str) -> list[dict[str, str]]:
        """Load a TSV file and return the content as a list of dictionaries"""
        with open(file_path, encoding=encoding, newline="") as f:
            try:
                reader = csv.DictReader(f, delimiter="\t")
                return list(reader)
            except Exception as e:
                raise BakufuError(
                    f"Error parsing TSV file '{file_path}': {e}", "INVALID_TSV_FORMAT"
                ) from e
