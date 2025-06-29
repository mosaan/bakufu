"""Array transformation text processing step"""

from typing import Any, Literal

from pydantic import Field

from .base import TextProcessStep


class ArrayTransformStep(TextProcessStep):
    """Array transformation text processing step"""

    method: Literal["array_transform"] = "array_transform"
    transform_expression: str = Field(..., description="Transform expression")

    async def process(self, input_data: Any, step_id: str) -> list[Any]:
        """Transform array elements"""
        from ..exceptions import ErrorContext, StepExecutionError

        if not isinstance(input_data, list):
            raise StepExecutionError(
                message="Input must be an array for array_transform",
                step_id=step_id,
                context=ErrorContext(step_id=step_id, function_name="ArrayTransformStep.process"),
                suggestions=["Provide an array as input"],
            )

        if not self.transform_expression:
            return input_data

        transformed = []
        for item in input_data:
            try:
                result = await self._apply_transform(item, self.transform_expression)
                transformed.append(result)
            except Exception as e:
                raise StepExecutionError(
                    message=f"Error applying transform: {e}",
                    step_id=step_id,
                    context=ErrorContext(
                        step_id=step_id, function_name="ArrayTransformStep.process"
                    ),
                    original_error=e,
                    suggestions=["Check transform expression syntax"],
                ) from e

        return transformed

    async def _apply_transform(self, item: Any, expression: str) -> Any:
        """Apply transformation expression to an item"""
        # Simple expression evaluation
        if isinstance(item, dict):
            # Replace item.key with item["key"] in expression
            import re

            expr_eval = expression
            for key in item:
                pattern = rf"item\.{key}\b"
                replacement = f'item["{key}"]'
                expr_eval = re.sub(pattern, replacement, expr_eval)

            # Evaluate the expression
            try:
                return eval(expr_eval, {"item": item})
            except Exception:
                # Fallback to original item
                return item
        else:
            # For non-dict items, replace 'item' with the actual value
            try:
                return eval(expression, {"item": item})
            except Exception:
                return item
