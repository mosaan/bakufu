"""Unified CSV/TSV parsing text processing step

This module consolidates csv_parse.py and tsv_parse.py into a single,
flexible CSV/TSV processing step that eliminates mechanical splitting.
"""

from typing import Any, Literal

from pydantic import Field

from ..csv_parsing import CsvParsingOptions, CsvProcessor
from .base import TextProcessStep


class CsvParseStep(TextProcessStep):
    """Unified CSV/TSV parsing text processing step

    Replaces separate csv_parse.py and tsv_parse.py files with a single
    configurable step following Martin Fowler's consolidation patterns.
    """

    method: Literal["csv_parse", "tsv_parse"] = "csv_parse"
    delimiter: str | None = Field(
        None, description="Delimiter character. None=auto-detect, ','=CSV, '\\t'=TSV"
    )
    strict_validation: bool = Field(True, description="Whether to enforce consistent column count")

    async def process(self, input_data: str, step_id: str) -> Any:
        """Parse CSV/TSV from text with unified options"""
        options = CsvParsingOptions(
            delimiter=self._resolve_delimiter(),
            step_id=step_id,
            strict_validation=self.strict_validation,
            context_type=self._get_context_type(),
        )
        return CsvProcessor.parse_csv_string(input_data, options)

    def _resolve_delimiter(self) -> str | None:
        """Resolve the delimiter based on method and configuration"""
        if self.delimiter is not None:
            return self.delimiter
        elif self.method == "tsv_parse":
            return "\t"
        else:
            return None  # Auto-detect for CSV

    def _get_context_type(self) -> Literal["csv", "tsv", "auto"]:
        """Get the context type based on method"""
        if self.method == "tsv_parse":
            return "tsv"
        elif self.method == "csv_parse":
            return "csv"
        else:
            return "auto"


# Alias for backward compatibility with TSV
class TsvParseStep(CsvParseStep):
    """TSV parsing step - alias for CsvParseStep with TSV defaults"""

    method: Literal["tsv_parse"] = "tsv_parse"
