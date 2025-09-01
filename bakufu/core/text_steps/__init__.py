"""Text processing steps module"""

from .array_aggregate import ArrayAggregateStep
from .array_filter import ArrayFilterStep
from .array_sort import ArraySortStep
from .array_transform import ArrayTransformStep
from .base import TextProcessStep
from .csv_parse import CsvParseStep, TsvParseStep
from .extract_between_marker import ExtractBetweenMarkerStep
from .fixed_split import FixedSplitStep
from .json_parse import JsonParseStep
from .markdown_split import MarkdownSplitStep
from .parse_as_json import ParseAsJsonStep
from .regex_extract import RegexExtractStep
from .replace import ReplaceStep
from .select_item import SelectItemStep
from .split import SplitStep
from .yaml_parse import YamlParseStep

# Type alias for any text processing step
AnyTextProcessStep = (
    TextProcessStep
    | RegexExtractStep
    | ReplaceStep
    | JsonParseStep
    | MarkdownSplitStep
    | FixedSplitStep
    | ArrayFilterStep
    | ArrayTransformStep
    | ArrayAggregateStep
    | ArraySortStep
    | SplitStep
    | ExtractBetweenMarkerStep
    | SelectItemStep
    | ParseAsJsonStep
    | CsvParseStep
    | TsvParseStep
    | YamlParseStep
)

__all__ = [
    "AnyTextProcessStep",
    "ArrayAggregateStep",
    "ArrayFilterStep",
    "ArraySortStep",
    "ArrayTransformStep",
    "CsvParseStep",
    "ExtractBetweenMarkerStep",
    "FixedSplitStep",
    "JsonParseStep",
    "MarkdownSplitStep",
    "ParseAsJsonStep",
    "RegexExtractStep",
    "ReplaceStep",
    "SelectItemStep",
    "SplitStep",
    "TextProcessStep",
    "TsvParseStep",
    "YamlParseStep",
]
