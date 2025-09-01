"""Base class for text processing steps"""

from abc import ABC, abstractmethod
from typing import Any, Literal

from pydantic import Field

from ..base_types import WorkflowStep


class TextProcessStep(WorkflowStep, ABC):
    """Text processing step with polymorphic behavior"""

    type: Literal["text_process"] = "text_process"
    method: Literal[
        "regex_extract",
        "replace",
        "json_parse",
        "markdown_split",
        "fixed_split",
        "array_filter",
        "array_transform",
        "array_aggregate",
        "array_sort",
        "split",
        "extract_between_marker",
        "select_item",
        "parse_as_json",
        "csv_parse",
        "tsv_parse",
        "yaml_parse",
    ]
    input: str = Field(..., description="Input text with template syntax")

    @abstractmethod
    async def process(self, input_data: Any, step_id: str) -> Any:
        """Process the input data and return the result"""
        pass
