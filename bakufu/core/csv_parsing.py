"""CSV/TSV parsing unified implementation with proper Parameter Object pattern

This module implements Martin Fowler's Parameter Object pattern to eliminate
mechanical splitting of CSV processing into 8 interdependent classes.
"""

import csv
from dataclasses import dataclass
from io import StringIO
from typing import Any, Literal

from .exceptions import BakufuError, ErrorContext, StepExecutionError


@dataclass
class CsvParsingOptions:
    """Parameter Object for CSV/TSV parsing configuration

    Replaces the mechanical splitting of parameters across multiple classes
    following Martin Fowler's Introduce Parameter Object refactoring pattern.
    """

    delimiter: str | None = None  # None=auto-detect, ","=CSV, "\t"=TSV
    step_id: str | None = None
    strict_validation: bool = True
    encoding: str = "utf-8"
    context_type: Literal["csv", "tsv", "auto"] = "auto"

    @property
    def is_step_context(self) -> bool:
        """Check if this is a step execution context"""
        return self.step_id is not None

    def resolve_delimiter(self, data: str) -> str:
        """Resolve the actual delimiter to use"""
        if self.delimiter is not None:
            return self.delimiter
        elif self.context_type == "tsv":
            return "\t"
        elif self.context_type == "csv":
            return ","
        else:
            # Auto-detect delimiter
            return self._detect_delimiter(data)

    def _detect_delimiter(self, data: str) -> str:
        """Auto-detect CSV delimiter from data"""
        sample = data[:1000]  # Use first 1000 chars for detection

        # Count occurrences of common delimiters
        delimiters = [",", "\t", ";", "|"]
        delimiter_counts = {}

        for delimiter in delimiters:
            delimiter_counts[delimiter] = sample.count(delimiter)

        # Return the most frequent delimiter, default to comma
        best_delimiter = max(delimiter_counts.items(), key=lambda x: x[1])
        return best_delimiter[0] if best_delimiter[1] > 0 else ","


class CsvProcessor:
    """Unified CSV/TSV processor eliminating mechanical class splitting

    Consolidates functionality from 8 previously split classes:
    - CsvParsingContext (eliminated - integrated into CsvParsingOptions)
    - CsvErrorHandler hierarchy (eliminated - consolidated into methods)
    - CsvStructureValidator (eliminated - integrated into main logic)
    - CsvParser (integrated here)
    - Original CsvProcessor (replaced)
    """

    @staticmethod
    def parse_csv_string(data: str, options: CsvParsingOptions) -> list[dict[str, Any]]:
        """Parse CSV/TSV string with unified options

        Args:
            data: CSV/TSV string data
            options: Parsing configuration

        Returns:
            List of dictionaries representing rows

        Raises:
            StepExecutionError: When step_id is provided and parsing fails
            BakufuError: When direct call and parsing fails
        """
        try:
            delimiter = options.resolve_delimiter(data)

            # Parse CSV data
            reader = csv.DictReader(StringIO(data.strip()), delimiter=delimiter)
            result = []

            # Read data with structure validation
            expected_fieldnames = None
            expected_field_count = 0
            for row_num, row in enumerate(reader, start=1):
                if expected_fieldnames is None:
                    expected_fieldnames = list(row.keys())
                    expected_field_count = len(expected_fieldnames)

                # Validate row structure if strict validation is enabled
                if options.strict_validation:
                    actual_field_count = len([v for v in row.values() if v is not None])
                    if actual_field_count != expected_field_count:
                        CsvProcessor._handle_structure_error(
                            row_num, actual_field_count, expected_field_count, options
                        )

                # Clean up None values and add to result
                cleaned_row = {k: v if v is not None else "" for k, v in row.items()}
                result.append(cleaned_row)

            return result

        except Exception as e:
            if isinstance(e, StepExecutionError | BakufuError):
                raise
            CsvProcessor._handle_parsing_error(e, data, options)
            return []  # This line should never be reached

    @staticmethod
    def _handle_structure_error(
        row_num: int, actual_fields: int, expected_fields: int, options: CsvParsingOptions
    ) -> None:
        """Handle CSV structure validation errors

        Consolidates functionality from StepContextErrorHandler and DirectCallErrorHandler
        using simple conditional logic instead of inheritance hierarchy.
        """
        error_msg = f"Row {row_num} has {actual_fields} fields, expected {expected_fields}"

        if options.is_step_context:
            assert options.step_id is not None  # Guaranteed by is_step_context
            raise StepExecutionError(
                message=f"Error parsing CSV: {error_msg}",
                step_id=options.step_id,
                context=ErrorContext(
                    step_id=options.step_id, function_name="CsvProcessor.parse_csv_string"
                ),
                suggestions=["Check CSV format and ensure consistent column count"],
            )
        else:
            raise BakufuError(
                message=f"Invalid CSV format: {error_msg}",
                error_code="INVALID_CSV_FORMAT",
                context=ErrorContext(function_name="CsvProcessor.parse_csv_string"),
                suggestions=["Check CSV format and ensure consistent column count"],
            )

    @staticmethod
    def _handle_parsing_error(e: Exception, data: str, options: CsvParsingOptions) -> None:
        """Handle general CSV parsing errors

        Consolidates error handling logic from multiple error handler classes.
        """
        if options.is_step_context:
            assert options.step_id is not None  # Guaranteed by is_step_context
            raise StepExecutionError(
                message=f"Error parsing CSV: {e}",
                step_id=options.step_id,
                context=ErrorContext(
                    step_id=options.step_id, function_name="CsvProcessor.parse_csv_string"
                ),
                original_error=e,
                suggestions=[
                    "Check CSV format and delimiters",
                    "Verify headers are present",
                    "Ensure consistent column count",
                    f"Text preview: {data.strip()[:100]}...",
                ],
            ) from e
        else:
            raise BakufuError(f"Error parsing CSV: {e}", "INVALID_CSV_FORMAT") from e


# Convenience functions for backward compatibility
def parse_csv(data: str, delimiter: str = ",", step_id: str | None = None) -> list[dict[str, Any]]:
    """Parse CSV string with convenience interface"""
    options = CsvParsingOptions(delimiter=delimiter, step_id=step_id, context_type="csv")
    return CsvProcessor.parse_csv_string(data, options)


def parse_tsv(data: str, step_id: str | None = None) -> list[dict[str, Any]]:
    """Parse TSV string with convenience interface"""
    options = CsvParsingOptions(delimiter="\t", step_id=step_id, context_type="tsv")
    return CsvProcessor.parse_csv_string(data, options)
