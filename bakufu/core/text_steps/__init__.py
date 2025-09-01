"""Text processing steps module"""

# Import all step classes to trigger registration
from ..step_registry import get_global_registry  # noqa: F401
from .base import TextProcessStep
from .csv_parse import CsvParseStep, TsvParseStep
from .extract_between_marker import ExtractBetweenMarkerStep
from .fixed_split import FixedSplitStep
from .format import FormatStep
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
    | SplitStep
    | ExtractBetweenMarkerStep
    | SelectItemStep
    | ParseAsJsonStep
    | FormatStep
    | CsvParseStep
    | TsvParseStep
    | YamlParseStep
)

__all__ = [
    "AnyTextProcessStep",
    "CsvParseStep",
    "ExtractBetweenMarkerStep",
    "FixedSplitStep",
    "FormatStep",
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
