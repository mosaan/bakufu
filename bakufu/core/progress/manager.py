"""Progress manager for orchestrating all progress displays."""

import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from .environment import EnvironmentType, detect_environment
from .models import (
    AIMapProgressData,
    ProgressStats,
    ProgressStatus,
    StepProgressData,
    WorkflowProgressData,
)

# Constants
MAX_ITEM_DISPLAY_LENGTH = 50
BATCH_LOG_FREQUENCY = 5


class ProgressManager:
    """Manages progress display across all execution levels."""

    def __init__(self, console: Console | None = None):
        self.console = console or Console()
        self.environment = detect_environment()
        self.interactive = self.environment == EnvironmentType.INTERACTIVE

        # Progress tracking
        self.workflow_data: WorkflowProgressData | None = None
        self.step_data: StepProgressData | None = None
        self.ai_map_data: AIMapProgressData | None = None

        # Rich components for interactive mode
        self.progress: Progress | None = None
        self.live_display: Live | None = None
        self.workflow_task: TaskID | None = None
        self.step_task: TaskID | None = None
        self.ai_map_task: TaskID | None = None

        # Callback for progress updates
        self.update_callback: Callable | None = None

    @contextmanager
    def workflow_progress(self, workflow_name: str, total_steps: int) -> Generator[Any, None, None]:
        """Context manager for workflow-level progress tracking."""
        self.start_workflow(workflow_name, total_steps)
        try:
            yield self
        finally:
            self.finish_workflow()

    def start_workflow(self, workflow_name: str, total_steps: int) -> None:
        """Start workflow-level progress tracking."""
        self.workflow_data = WorkflowProgressData(
            workflow_name=workflow_name,
            current_step=0,
            total_steps=total_steps,
            current_step_name="",
            current_step_type="",
            total_errors=0,
            start_time=time.time(),
            status=ProgressStatus.RUNNING,
        )

        if self.interactive:
            self._setup_interactive_display()
        else:
            self._log_workflow_start()

    def update_workflow_step(self, current_step: int, step_name: str, step_type: str) -> None:
        """Update current workflow step."""
        if self.workflow_data:
            self.workflow_data.current_step = current_step
            self.workflow_data.current_step_name = step_name
            self.workflow_data.current_step_type = step_type

            if self.interactive and self.workflow_task and self.progress:
                self.progress.update(
                    self.workflow_task,
                    completed=current_step,
                    description=f"🚀 {self.workflow_data.workflow_name}: {step_name}",
                )
            else:
                self._log_step_start(current_step, step_name, step_type)

    def finish_workflow(self, success: bool = True) -> None:
        """Finish workflow progress tracking."""
        if self.workflow_data:
            total_time = time.time() - self.workflow_data.start_time
            self.workflow_data.status = (
                ProgressStatus.COMPLETED if success else ProgressStatus.FAILED
            )

            if self.interactive:
                self._cleanup_interactive_display()

            self._log_workflow_complete(success, total_time)

        # Reset state
        self.workflow_data = None
        self.step_data = None
        self.ai_map_data = None

    def start_step(self, step_id: str, step_type: str, description: str) -> None:
        """Start step-level progress tracking."""
        self.step_data = StepProgressData(
            step_id=step_id,
            step_type=step_type,
            description=description,
            progress_percent=0.0,
            current_operation="Starting...",
            errors=0,
            start_time=time.time(),
            status=ProgressStatus.RUNNING,
        )

        if not self.interactive:
            self._log_step_progress()

    def update_step_progress(
        self, progress_percent: float, operation: str, errors: int = 0
    ) -> None:
        """Update step progress."""
        if self.step_data:
            self.step_data.progress_percent = progress_percent
            self.step_data.current_operation = operation
            self.step_data.errors = errors

            if self.interactive and self.step_task and self.progress:
                self.progress.update(
                    self.step_task,
                    completed=int(progress_percent),
                    description=f"📝 {self.step_data.description}: {operation}",
                )

    def finish_step(self, success: bool = True, stats: ProgressStats | None = None) -> None:
        """Finish step progress tracking."""
        if self.step_data:
            total_time = time.time() - self.step_data.start_time
            self.step_data.status = ProgressStatus.COMPLETED if success else ProgressStatus.FAILED

            if not self.interactive:
                self._log_step_complete(success, total_time, stats)

        self.step_data = None
        self.ai_map_data = None

    def _setup_interactive_display(self) -> None:
        """Setup Rich interactive progress display."""
        if not self.workflow_data:
            return

        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console,
            expand=True,
        )

        self.workflow_task = self.progress.add_task(
            f"🚀 {self.workflow_data.workflow_name}", total=self.workflow_data.total_steps
        )

        self.step_task = self.progress.add_task("📝 Step", total=100, visible=False)

        self.live_display = Live(self.progress, console=self.console, refresh_per_second=4)
        self.live_display.start()

    def _cleanup_interactive_display(self) -> None:
        """Cleanup Rich interactive display."""
        if self.live_display:
            self.live_display.stop()
            self.live_display = None

        self.progress = None
        self.workflow_task = None
        self.step_task = None
        self.ai_map_task = None

    def _log_workflow_start(self) -> None:
        """Log workflow start in non-interactive mode."""
        if self.workflow_data:
            self.console.print(
                f'[WORKFLOW] Starting: "{self.workflow_data.workflow_name}" '
                f"({self.workflow_data.total_steps} steps)"
            )

    def _log_step_start(self, current_step: int, step_name: str, step_type: str) -> None:
        """Log step start in non-interactive mode."""
        if self.workflow_data:
            self.console.print(
                f"[STEP {current_step}/{self.workflow_data.total_steps}] "
                f"{step_type}: {step_name} - Starting..."
            )

    def _log_step_progress(self) -> None:
        """Log step progress in non-interactive mode."""
        if self.step_data:
            self.console.print(
                f"[{self.step_data.step_type.upper()}] "
                f"{self.step_data.description}: {self.step_data.current_operation}"
            )

    def _log_step_complete(
        self, success: bool, total_time: float, stats: ProgressStats | None
    ) -> None:
        """Log step completion in non-interactive mode."""
        if self.step_data:
            status = "✅ Completed" if success else "❌ Failed"
            self.console.print(f"[{self.step_data.step_type.upper()}] {status} ({total_time:.1f}s)")

    def _log_ai_map_start(self, total_items: int, total_batches: int) -> None:
        """Log AI Map Call start in non-interactive mode."""
        self.console.print(
            f"[AI_MAP_CALL] Processing {total_items} items in {total_batches} batches..."
        )

    def _log_ai_map_progress(self) -> None:
        """Log AI Map Call progress in non-interactive mode."""
        if not self.ai_map_data:
            return

        total_processed = self.ai_map_data.completed_items + self.ai_map_data.failed_items
        self.console.print(
            f"[BATCH {self.ai_map_data.current_batch}/{self.ai_map_data.total_batches}] "
            f"Items {total_processed}/{self.ai_map_data.total_items} "
            f"({self.ai_map_data.success_rate:.1f}% success)"
        )

    def _log_ai_map_complete(self) -> None:
        """Log AI Map Call completion in non-interactive mode."""
        if not self.ai_map_data:
            return

        total_time = time.time() - self.ai_map_data.start_time
        self.console.print(
            f"[AI_MAP_CALL] ✅ Completed: "
            f"{self.ai_map_data.completed_items}/{self.ai_map_data.total_items} success "
            f"({self.ai_map_data.success_rate:.1f}%) in {total_time:.1f}s"
        )

    def _log_workflow_complete(self, success: bool, total_time: float) -> None:
        """Log workflow completion in non-interactive mode."""
        if self.workflow_data:
            status = "✅ Completed" if success else "❌ Failed"
            self.console.print(f"[WORKFLOW] {status} in {total_time:.1f}s")
