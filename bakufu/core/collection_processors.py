"""Collection operations processor implementation with functional programming approach"""

import asyncio
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from .exceptions import StepExecutionError

if TYPE_CHECKING:
    from .models import (
        CollectionResult,
        CollectionStep,
        ExecutionContext,
    )


class CollectionProcessor:
    """Base processor for collection operations"""

    def __init__(self, step: "CollectionStep", progress_callback: Callable | None = None):
        self.step = step
        self.progress_callback = progress_callback
        self.start_time = 0.0
        self.processing_stats: dict[str, Any] = {}

    async def process(self, input_data: Any, context: "ExecutionContext") -> "CollectionResult":
        """Process collection operation and return CollectionResult"""
        from .models import CollectionResult

        self.start_time = time.time()

        try:
            # Evaluate input
            if isinstance(input_data, str):
                evaluated_input = context.render_template_object(input_data)
            else:
                evaluated_input = input_data

            if not isinstance(evaluated_input, list):
                raise StepExecutionError(
                    message=f"Collection input must be a list, got {type(evaluated_input)}",
                    step_id=self.step.id,
                    workflow_name=context.workflow_name,
                )

            result = await self._dispatch_operation(evaluated_input, context)

            # Calculate processing stats
            processing_time = time.time() - self.start_time
            self.processing_stats = {
                "processing_time": processing_time,
                "operation": self.step.operation,
                "input_count": len(evaluated_input),
                "output_count": len(result) if isinstance(result, list) else 1,
            }

            return CollectionResult(
                output=result,
                operation=self.step.operation,
                input_count=len(evaluated_input),
                output_count=len(result) if isinstance(result, list) else 1,
                processing_stats=self.processing_stats,
                errors=[],
            )

        except Exception as e:
            raise StepExecutionError(
                message=f"Collection operation failed: {e!s}",
                step_id=self.step.id,
                workflow_name=context.workflow_name,
                original_error=e,
            ) from e

    async def _dispatch_operation(self, evaluated_input: Any, context: "ExecutionContext") -> Any:
        from .models import FilterOperation, MapOperation, ReduceOperation

        if self.step.operation == "map":
            return await self._process_map(evaluated_input, context)
        if self.step.operation == "filter":
            return await self._process_filter(evaluated_input, context)
        if self.step.operation == "reduce":
            return await self._process_reduce(evaluated_input, context)
        if self.step.operation == "pipeline":
            pipeline_ops = getattr(self.step, "pipeline", [])
            current_input = evaluated_input
            for idx, op in enumerate(pipeline_ops):
                op_type = op.get("operation")
                op_id = op.get("id", f"pipeline_{self.step.id}_{idx}")
                op_with_id = {**op, "input": "{{ input }}", "id": op_id}
                if op_type == "map":
                    step_obj: CollectionStep = MapOperation(**op_with_id)
                elif op_type == "filter":
                    step_obj = FilterOperation(**op_with_id)
                elif op_type == "reduce":
                    step_obj = ReduceOperation(**op_with_id)
                else:
                    raise StepExecutionError(
                        message=f"Unsupported operation in pipeline: {op_type}",
                        step_id=self.step.id,
                        workflow_name=context.workflow_name,
                    )
                processor = CollectionProcessor(step_obj)
                sub_context = context.model_copy(deep=True)
                sub_context.input_data = {**context.input_data, "input": current_input}
                sub_result = await processor.process(current_input, sub_context)
                current_input = sub_result.output
            return current_input
        raise StepExecutionError(
            message=f"Unsupported collection operation: {self.step.operation}",
            step_id=self.step.id,
            workflow_name=context.workflow_name,
        )

    async def _process_map(self, input_list: list[Any], context: "ExecutionContext") -> list[Any]:
        """Process map operation - transform each element"""
        from .execution_engine import WorkflowExecutionEngine

        if not hasattr(self.step, "steps"):
            raise StepExecutionError(
                message="Map operation requires 'steps' field",
                step_id=self.step.id,
                workflow_name=context.workflow_name,
            )

        results = []
        engine = WorkflowExecutionEngine()

        # Check if concurrency is configured for parallel processing
        if (
            hasattr(self.step, "concurrency")
            and self.step.concurrency
            and isinstance(self.step.concurrency, dict)
            and self.step.concurrency.get("max_parallel", 1) > 1
        ):
            results = await self._process_map_parallel(input_list, context, engine)
        else:
            # Sequential processing
            for i, item in enumerate(input_list):
                try:
                    item_result = await self._process_map_item(item, context, engine, i)
                    results.append(item_result)
                except Exception:
                    if self.step.error_handling.on_item_failure == "stop":
                        raise
                    elif self.step.error_handling.on_item_failure == "skip":
                        results.append(None)  # Preserve order with None for failed items
                    # 'retry' logic would go here if needed

        return results

    async def _process_map_parallel(
        self, input_list: list[Any], context: "ExecutionContext", engine: Any
    ) -> list[Any]:
        """Process map operation with parallel execution"""
        max_parallel = 3
        if self.step.concurrency and isinstance(self.step.concurrency, dict):
            max_parallel = self.step.concurrency.get("max_parallel", 3)
        semaphore = asyncio.Semaphore(max_parallel)
        results = [None] * len(input_list)  # Pre-allocate to preserve order

        async def process_item_with_semaphore(item: Any, index: int) -> None:
            async with semaphore:
                try:
                    result = await self._process_map_item(item, context, engine, index)
                    results[index] = result
                except Exception:
                    if self.step.error_handling.on_item_failure == "stop":
                        raise
                    elif self.step.error_handling.on_item_failure == "skip":
                        results[index] = None

        # Create tasks for all items
        tasks = [process_item_with_semaphore(item, i) for i, item in enumerate(input_list)]
        # Wait for all tasks to complete
        await asyncio.gather(*tasks, return_exceptions=True)
        return results

    async def _process_map_item(
        self, item: Any, context: "ExecutionContext", engine: Any, index: int
    ) -> Any:
        """Process a single item through the map steps"""
        # Create a new context for this item with 'item' variable
        item_context = context.model_copy(deep=True)
        item_context.input_data = {**context.input_data, "item": item}

        # Execute steps for this item
        step_results = {}
        steps = getattr(self.step, "steps", [])
        for step in steps:
            result = await engine.execute_step(step, item_context)
            step_results[step.id] = result
            item_context.set_step_output(step.id, result)

        # Return the result of the last step
        if step_results:
            last_step_id = list(step_results.keys())[-1]
            return step_results[last_step_id]
        return None

    async def _process_filter(
        self, input_list: list[Any], context: "ExecutionContext"
    ) -> list[Any]:
        """Process filter operation - select elements matching condition"""
        condition = getattr(self.step, "condition", None)
        if condition is None:
            raise StepExecutionError(
                message="Filter operation requires 'condition' field",
                step_id=self.step.id,
                workflow_name=context.workflow_name,
            )

        results = []

        for item in input_list:
            try:
                # Create context with item variable
                filter_context = {**context.get_template_context(), "item": item}
                # Evaluate condition
                condition_result = context._template_engine.render_object(condition, filter_context)

                # Convert to boolean - handle string results from template engine
                if isinstance(condition_result, str):
                    # If result is a string representation of boolean
                    condition_bool = condition_result.lower() in ("true", "1", "yes", "on")
                else:
                    condition_bool = bool(condition_result)
                if condition_bool:
                    results.append(item)

            except Exception as e:
                if self.step.error_handling.on_condition_error == "stop":
                    raise StepExecutionError(
                        message=f"Filter condition evaluation failed: {e!s}",
                        step_id=self.step.id,
                        workflow_name=context.workflow_name,
                        original_error=e,
                    ) from e
                elif self.step.error_handling.on_condition_error == "skip_item":
                    continue  # Skip this item
                elif self.step.error_handling.on_condition_error == "default_false":
                    continue

        return results

    async def _process_reduce(self, input_list: list[Any], context: "ExecutionContext") -> Any:
        """Process reduce operation - aggregate elements into single value"""
        from .execution_engine import WorkflowExecutionEngine

        if not hasattr(self.step, "steps"):
            raise StepExecutionError(
                message="Reduce operation requires 'steps' field",
                step_id=self.step.id,
                workflow_name=context.workflow_name,
            )

        # Initialize accumulator
        accumulator = getattr(self.step, "initial_value", None)
        accumulator_var = getattr(self.step, "accumulator_var", "acc")
        item_var = getattr(self.step, "item_var", "item")
        engine = WorkflowExecutionEngine()
        for item in input_list:
            # Create context with accumulator and item variables
            reduce_context = context.model_copy(deep=True)
            reduce_context.input_data = {
                **context.input_data,
                accumulator_var: accumulator,
                item_var: item,
            }

            # Execute steps for this reduction
            step_results = {}
            steps = getattr(self.step, "steps", [])
            for step in steps:
                result = await engine.execute_step(step, reduce_context)
                step_results[step.id] = result
                reduce_context.set_step_output(step.id, result)
            # Update accumulator with result of last step
            if step_results:
                last_step_id = list(step_results.keys())[-1]
                accumulator = step_results[last_step_id]

        return accumulator
