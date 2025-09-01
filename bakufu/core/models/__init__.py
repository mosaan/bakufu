"""Bakufu workflow models - domain-separated for better maintainability"""

# Import AnyTextProcessStep for type resolution
from ..text_steps import AnyTextProcessStep

# Base types and common definitions
from .base import AnyWorkflowStep, InputParameter, OutputFormat, StructuredInputValue

# Execution context and usage tracking
from .execution import ExecutionContext, UsageSummary

# Operation results
from .results import CollectionResult, ConditionalResult

# Step definitions
from .steps import (
    AICallStep,
    CollectionErrorHandling,
    CollectionStep,
    ConditionalBranch,
    ConditionalStep,
    FilterOperation,
    MapOperation,
    PipelineOperation,
    ReduceOperation,
)

# Workflow definitions
from .workflow import Workflow, WorkflowConfig

__all__ = [
    "AICallStep",
    "AnyTextProcessStep",
    "AnyWorkflowStep",
    "CollectionErrorHandling",
    "CollectionResult",
    "CollectionStep",
    "ConditionalBranch",
    "ConditionalResult",
    "ConditionalStep",
    "ExecutionContext",
    "FilterOperation",
    "InputParameter",
    "MapOperation",
    "OutputFormat",
    "PipelineOperation",
    "ReduceOperation",
    "StructuredInputValue",
    "UsageSummary",
    "Workflow",
    "WorkflowConfig",
]

# Rebuild models to resolve forward references
Workflow.model_rebuild()
ConditionalStep.model_rebuild()
ConditionalBranch.model_rebuild()
MapOperation.model_rebuild()
ReduceOperation.model_rebuild()
