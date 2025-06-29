"""Progress tracking data models."""

from dataclasses import dataclass
from enum import Enum


class ProgressStatus(Enum):
    """Status of a progress item."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowProgressData:
    """Progress data for overall workflow execution."""

    workflow_name: str
    current_step: int
    total_steps: int
    current_step_name: str
    current_step_type: str
    total_errors: int
    start_time: float
    estimated_completion: float | None = None
    status: ProgressStatus = ProgressStatus.RUNNING


@dataclass
class StepProgressData:
    """Progress data for individual step execution."""

    step_id: str
    step_type: str
    description: str
    progress_percent: float
    current_operation: str
    errors: int
    start_time: float
    status: ProgressStatus = ProgressStatus.RUNNING
    total_items: int | None = None
    completed_items: int | None = None


@dataclass
class AIMapProgressData:
    """Progress data for AI Map Call execution."""

    total_items: int
    completed_items: int
    failed_items: int
    current_batch: int
    total_batches: int
    current_item_description: str
    active_parallel_count: int
    success_rate: float
    average_time_per_item: float
    total_retries: int
    api_calls: int
    total_tokens: int
    estimated_cost: float
    start_time: float
    status: ProgressStatus = ProgressStatus.RUNNING


@dataclass
class ProgressStats:
    """Overall progress statistics."""

    total_time: float
    api_calls: int
    total_tokens: int
    estimated_cost: float
    success_rate: float
    error_count: int
    retry_count: int


@dataclass
class AIMapUpdateData:
    """Data container for AI Map Call progress updates."""

    completed: int
    failed: int
    current_item: str
    current_batch: int
    active_parallel: int
    retries: int = 0
    api_calls: int = 0
    tokens: int = 0
    cost: float = 0.0
