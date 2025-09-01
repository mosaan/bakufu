"""Common text processing utilities for bakufu

This module provides unified text processing functionality that can be shared
between input file processing and workflow text processing steps.
"""

import csv
import json
import re
from dataclasses import dataclass
from io import StringIO
from typing import Any, Literal

import yaml

from .exceptions import BakufuError, ErrorContext, StepExecutionError


@dataclass
class CsvParsingContext:
    """CSV解析コンテキスト情報"""

    context: str  # "direct call" or "step"
    step_id: str | None = None

    @property
    def is_step_context(self) -> bool:
        """ステップコンテキストかどうかを判定"""
        return self.step_id is not None


class JsonProcessor:
    """Unified JSON processing with consistent error handling"""

    @staticmethod
    def parse_json_string(
        data: str, context: str = "JSON parsing", step_id: str | None = None
    ) -> Any:
        """Parse JSON from string with consistent error handling"""
        try:
            return json.loads(data.strip())
        except json.JSONDecodeError as e:
            if step_id:
                raise StepExecutionError(
                    message=f"Invalid JSON format: {e}",
                    step_id=step_id,
                    context=ErrorContext(
                        step_id=step_id, function_name="JsonProcessor.parse_json_string"
                    ),
                    original_error=e,
                    suggestions=[
                        "Check JSON syntax and quotes",
                        "Verify JSON structure is valid",
                        "Ensure all strings are properly quoted",
                        f"Text preview: {data.strip()[:100]}...",
                    ],
                ) from e
            else:
                raise BakufuError(f"Invalid JSON in {context}: {e}", "INVALID_JSON_FORMAT") from e

    @staticmethod
    def parse_json_file(file_path: str, encoding: str = "utf-8") -> Any:
        """Parse JSON from file with consistent error handling"""
        with open(file_path, encoding=encoding) as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as e:
                raise BakufuError(
                    f"Invalid JSON in file '{file_path}': {e}", "INVALID_JSON_FORMAT"
                ) from e


class YamlProcessor:
    """Unified YAML processing with consistent error handling"""

    @staticmethod
    def parse_yaml_string(
        data: str, context: str = "YAML parsing", step_id: str | None = None
    ) -> Any:
        """Parse YAML from string with consistent error handling"""
        try:
            # Use a custom loader that doesn't auto-parse dates to maintain consistency
            class NoDateLoader(yaml.SafeLoader):
                pass

            # Add a custom constructor for timestamps that returns strings
            def timestamp_constructor(loader: yaml.Loader, node: yaml.ScalarNode) -> str:
                return loader.construct_scalar(node)

            NoDateLoader.add_constructor("tag:yaml.org,2002:timestamp", timestamp_constructor)

            return yaml.load(data.strip(), Loader=NoDateLoader)
        except yaml.YAMLError as e:
            if step_id:
                raise StepExecutionError(
                    message=f"Invalid YAML format: {e}",
                    step_id=step_id,
                    context=ErrorContext(
                        step_id=step_id, function_name="YamlProcessor.parse_yaml_string"
                    ),
                    original_error=e,
                    suggestions=[
                        "Check YAML syntax and indentation",
                        "Verify YAML structure is valid",
                        "Ensure proper key-value formatting",
                        f"Text preview: {data.strip()[:100]}...",
                    ],
                ) from e
            else:
                raise BakufuError(f"Invalid YAML in {context}: {e}", "INVALID_YAML_FORMAT") from e

    @staticmethod
    def parse_yaml_file(file_path: str, encoding: str = "utf-8") -> Any:
        """Parse YAML from file with consistent error handling"""
        with open(file_path, encoding=encoding) as f:
            try:
                # Use a custom loader that doesn't auto-parse dates to maintain consistency
                class NoDateLoader(yaml.SafeLoader):
                    pass

                # Remove date/datetime constructors to prevent auto-parsing
                NoDateLoader.yaml_constructors.pop("tag:yaml.org,2002:timestamp", None)

                return yaml.load(f, Loader=NoDateLoader)
            except yaml.YAMLError as e:
                raise BakufuError(
                    f"Invalid YAML in file '{file_path}': {e}", "INVALID_YAML_FORMAT"
                ) from e


class CsvErrorHandler:
    """CSV エラーハンドリングの基底クラス"""

    def handle_structure_error(
        self, row_num: int, actual_fields: int, expected_fields: int
    ) -> None:
        raise NotImplementedError

    def handle_parsing_error(self, e: Exception, data: str) -> None:
        raise NotImplementedError


class StepContextErrorHandler(CsvErrorHandler):
    """Step実行コンテキスト用のエラーハンドラー"""

    def __init__(self, step_id: str):
        self.step_id = step_id

    def handle_structure_error(
        self, row_num: int, actual_fields: int, expected_fields: int
    ) -> None:
        error_msg = f"Row {row_num} has {actual_fields} fields, expected {expected_fields}"
        raise StepExecutionError(
            message=f"Error parsing CSV: {error_msg}",
            step_id=self.step_id,
            context=ErrorContext(
                step_id=self.step_id,
                function_name="CsvProcessor.parse_csv_string",
            ),
            suggestions=["Check CSV format and ensure consistent column count"],
        )

    def handle_parsing_error(self, e: Exception, data: str) -> None:
        raise StepExecutionError(
            message=f"Error parsing CSV: {e}",
            step_id=self.step_id,
            context=ErrorContext(
                step_id=self.step_id, function_name="CsvProcessor.parse_csv_string"
            ),
            original_error=e,
            suggestions=[
                "Check CSV format and delimiters",
                "Verify headers are present",
                "Ensure consistent column count",
                f"Text preview: {data.strip()[:100]}...",
            ],
        ) from e


class DirectCallErrorHandler(CsvErrorHandler):
    """直接呼び出し用のエラーハンドラー"""

    def handle_structure_error(
        self, row_num: int, actual_fields: int, expected_fields: int
    ) -> None:
        error_msg = f"Row {row_num} has {actual_fields} fields, expected {expected_fields}"
        raise BakufuError(
            message=f"Invalid CSV format: {error_msg}",
            error_code="INVALID_CSV_FORMAT",
            context=ErrorContext(
                function_name="CsvProcessor.parse_csv_string",
            ),
            suggestions=["Check CSV format and ensure consistent column count"],
        )

    def handle_parsing_error(self, e: Exception, data: str) -> None:
        raise BakufuError(f"Error parsing CSV: {e}", "INVALID_CSV_FORMAT") from e


class CsvStructureValidator:
    """CSV構造の検証を担当"""

    def __init__(self, parsing_context: CsvParsingContext, error_handler: CsvErrorHandler):
        self.parsing_context = parsing_context
        self.error_handler = error_handler

    def validate(
        self, data: str, delimiter: str, reader: csv.DictReader, result: list[dict[str, str]]
    ) -> None:
        """CSV構造の検証を実行"""
        if not result or not reader.fieldnames:
            return

        expected_fields = len(reader.fieldnames)
        lines = data.strip().split("\n")[1:]  # Skip header

        for i, line in enumerate(lines):
            if not line.strip():
                continue
            actual_fields = len(line.split(delimiter))

            if self._should_error(actual_fields, expected_fields):
                self.error_handler.handle_structure_error(i + 2, actual_fields, expected_fields)

    def _should_error(self, actual_fields: int, expected_fields: int) -> bool:
        if self.parsing_context.is_step_context:
            return actual_fields < expected_fields
        else:
            return actual_fields != expected_fields


class CsvParser:
    """CSV解析の主要ロジックを担当"""

    def __init__(self, data: str, delimiter: str | None = None):
        self.data = data
        self.delimiter = delimiter or self._detect_delimiter(data)

    def parse(self, parsing_context: CsvParsingContext) -> list[dict[str, str]]:
        """CSV解析を実行"""
        if not self.data.strip():
            return []

        error_handler = self._create_error_handler(parsing_context)

        try:
            reader = csv.DictReader(StringIO(self.data), delimiter=self.delimiter)
            result = list(reader)

            if not result:
                lines = self.data.strip().split("\n")
                if len(lines) == 1:
                    return []

            validator = CsvStructureValidator(parsing_context, error_handler)
            validator.validate(self.data, self.delimiter, reader, result)

            return result
        except (StepExecutionError, BakufuError):
            raise
        except Exception as e:
            error_handler.handle_parsing_error(e, self.data)
            return []  # This should never be reached

    def _detect_delimiter(self, data: str) -> str:
        """区切り文字を自動検出"""
        sniffer = csv.Sniffer()
        try:
            sample = data[:1024]
            dialect = sniffer.sniff(sample, delimiters=",;\t|")
            return dialect.delimiter
        except csv.Error:
            return ","

    def _create_error_handler(self, parsing_context: CsvParsingContext) -> CsvErrorHandler:
        """コンテキストに応じたエラーハンドラーを作成"""
        if parsing_context.step_id:
            return StepContextErrorHandler(parsing_context.step_id)
        else:
            return DirectCallErrorHandler()


class CsvProcessor:
    """Unified CSV/TSV processing with consistent error handling"""

    @staticmethod
    def parse_csv_string(
        data: str,
        delimiter: str | None = None,
        step_id: str | None = None,
        context: str = "direct call",
    ) -> list[dict[str, str]]:
        """Parse CSV from string with delimiter detection"""
        parsing_context = CsvParsingContext(context=context, step_id=step_id)
        parser = CsvParser(data, delimiter)
        return parser.parse(parsing_context)

    @staticmethod
    def parse_csv_file(
        file_path: str, encoding: str = "utf-8", delimiter: str | None = None
    ) -> list[dict[str, str]]:
        """Parse CSV from file with delimiter detection"""
        with open(file_path, encoding=encoding, newline="") as f:
            try:
                if delimiter is None:
                    # Auto-detect delimiter
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

    @staticmethod
    def parse_tsv_string(data: str, step_id: str | None = None) -> list[dict[str, str]]:
        """Parse TSV from string"""
        return CsvProcessor.parse_csv_string(
            data, delimiter="\t", step_id=step_id, context="direct call"
        )

    @staticmethod
    def parse_tsv_file(file_path: str, encoding: str = "utf-8") -> list[dict[str, str]]:
        """Parse TSV from file"""
        with open(file_path, encoding=encoding, newline="") as f:
            try:
                reader = csv.DictReader(f, delimiter="\t")
                return list(reader)
            except Exception as e:
                raise BakufuError(
                    f"Error parsing TSV file '{file_path}': {e}", "INVALID_TSV_FORMAT"
                ) from e


class TextSplitter:
    """Unified text splitting utilities"""

    @staticmethod
    def split_by_separator(
        text: str, separator: str, max_splits: int = -1, preserve_empty: bool = False
    ) -> list[str]:
        """Split text by separator with options"""
        parts = text.split(separator, max_splits)
        if not preserve_empty:
            # Filter out empty parts, but preserve single empty string result from empty input
            filtered_parts = [part for part in parts if part.strip()]
            # If we filtered everything out but original had content, return empty list
            # If original was empty, preserve the single empty string
            if not filtered_parts and parts == [""]:
                return [""]
            return filtered_parts
        return parts

    @staticmethod
    def split_by_lines(text: str, preserve_empty: bool = False) -> list[str]:
        """Split text by lines with options"""
        lines = [line.rstrip("\n\r") for line in text.splitlines()]
        if not preserve_empty:
            lines = [line for line in lines if line.strip()]
        return lines

    @staticmethod
    def split_by_regex(
        text: str, pattern: str, max_splits: int = -1, preserve_empty: bool = False
    ) -> list[str]:
        """Split text by regex pattern"""
        import re as regex_module  # Clear import to avoid conflicts

        try:
            if max_splits == -1:
                parts = regex_module.split(pattern, text)
            else:
                parts = regex_module.split(pattern, text, maxsplit=max_splits)

            if not preserve_empty:
                parts = [part for part in parts if part]
            return parts
        except Exception:
            # Fallback to string split if regex fails
            return [text]

    @staticmethod
    def split_fixed_size(
        text: str, size: int, unit: Literal["characters", "words"] = "characters", overlap: int = 0
    ) -> list[str]:
        """Split text into fixed-size chunks"""
        if unit == "characters":
            return TextSplitter._split_by_characters(text, size, overlap)
        elif unit == "words":
            return TextSplitter._split_by_words(text, size, overlap)
        else:
            raise ValueError(f"Unsupported unit: {unit}")

    @staticmethod
    def _split_by_characters(text: str, size: int, overlap: int = 0) -> list[str]:
        """Split text by character count"""
        if size <= 0:
            raise ValueError("Size must be positive")
        if overlap >= size:
            raise ValueError("Overlap must be less than size")

        chunks = []
        start = 0

        while start < len(text):
            end = start + size
            chunk = text[start:end]

            # Only add if we have a meaningful chunk
            if chunk:
                chunks.append(chunk)

            if end >= len(text):
                break

            # Calculate next start position with overlap
            next_start = end - overlap

            # If next start would create a chunk that's too short and overlaps significantly,
            # try to adjust to get a fuller chunk
            if len(text) - next_start < size and len(text) - next_start > 0:
                # If remaining text is shorter than size but we have room to start earlier
                # to get a full-size chunk, do that
                potential_start = len(text) - size
                if potential_start > start and potential_start >= next_start - overlap:
                    start = potential_start
                else:
                    start = next_start
            else:
                start = next_start

        return chunks

    @staticmethod
    def _split_by_words(text: str, size: int, overlap: int = 0) -> list[str]:
        """Split text by word count"""
        if size <= 0:
            raise ValueError("Size must be positive")
        if overlap >= size:
            raise ValueError("Overlap must be less than size")

        words = text.split()
        chunks = []
        start = 0

        while start < len(words):
            end = start + size
            chunk_words = words[start:end]
            chunks.append(" ".join(chunk_words))

            if end >= len(words):
                break

            start = end - overlap

        return chunks


def extract_by_regex(text: str, pattern: str, group: int = 0, flags: int = 0) -> list[str]:
    """Extract text using regex pattern"""
    matches = re.finditer(pattern, text, flags)
    return [match.group(group) for match in matches]


def extract_between_markers(
    text: str, start_marker: str, end_marker: str, include_markers: bool = False
) -> list[str]:
    """Extract text between start and end markers

    Finds the innermost complete pairs when dealing with nested markers.
    For incomplete pairs, extracts the most complete available pairs.
    """
    results = []

    # Find all start and end marker positions
    start_positions = []
    end_positions = []

    pos = 0
    while pos < len(text):
        start_pos = text.find(start_marker, pos)
        if start_pos == -1:
            break
        start_positions.append(start_pos)
        pos = start_pos + 1

    pos = 0
    while pos < len(text):
        end_pos = text.find(end_marker, pos)
        if end_pos == -1:
            break
        end_positions.append(end_pos)
        pos = end_pos + 1

    # Match markers to find proper pairs
    used_starts = set()
    used_ends = set()

    # For each end marker, find the closest preceding start marker
    for end_idx in end_positions:
        best_start_idx = -1
        for start_idx in start_positions:
            if (
                start_idx < end_idx
                and start_idx not in used_starts
                and (best_start_idx == -1 or start_idx > best_start_idx)
            ):
                best_start_idx = start_idx

        if best_start_idx != -1:
            used_starts.add(best_start_idx)
            used_ends.add(end_idx)

            if include_markers:
                extracted = text[best_start_idx : end_idx + len(end_marker)]
            else:
                extracted = text[best_start_idx + len(start_marker) : end_idx]

            results.append(extracted)

    return results


def is_valid_json(text: str) -> bool:
    """Check if text is valid JSON"""
    try:
        json.loads(text.strip())
        return True
    except json.JSONDecodeError:
        return False


def is_valid_yaml(text: str) -> bool:
    """Check if text is valid YAML"""
    try:
        yaml.safe_load(text.strip())
        return True
    except yaml.YAMLError:
        return False


def detect_delimiter(text: str) -> str:
    """Detect CSV delimiter from text sample"""
    try:
        sniffer = csv.Sniffer()
        sample = text[:1024]
        delimiter = sniffer.sniff(sample).delimiter

        # Only accept common CSV delimiters from the sniffer
        if delimiter in [",", ";", "\t", "|"]:
            return delimiter

        # If sniffer detected something unusual, fall back to common delimiters
        for common_delimiter in [",", ";", "\t", "|"]:
            if common_delimiter in sample:
                # Check if this delimiter creates consistent columns across lines
                lines = sample.split("\n")[:3]  # Check first few lines
                if len(lines) > 1:
                    first_count = lines[0].count(common_delimiter)
                    if first_count > 0 and all(
                        line.count(common_delimiter) == first_count
                        for line in lines[1:]
                        if line.strip()
                    ):
                        return common_delimiter
                elif common_delimiter in lines[0]:
                    return common_delimiter

        return ","  # Default to comma
    except Exception:
        return ","  # Default to comma
