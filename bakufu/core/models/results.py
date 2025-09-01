"""Result models for Bakufu workflow operations"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CollectionResult:
    """Result of a collection operation"""

    output: Any = None
    operation: str | None = None
    input_count: int = 0
    output_count: int = 0
    processing_stats: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "output": self.output,
            "operation": self.operation,
            "input_count": self.input_count,
            "output_count": self.output_count,
            "processing_stats": self.processing_stats,
            "errors": self.errors,
        }


@dataclass
class ConditionalResult:
    """Result of a conditional step execution"""

    output: Any = None
    condition_result: bool | None = None
    executed_branch: str | None = None
    evaluation_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return as dictionary for Jinja2 template reference"""
        return {
            "output": self.output,
            "condition_result": self.condition_result,
            "executed_branch": self.executed_branch,
            "evaluation_error": self.evaluation_error,
        }
