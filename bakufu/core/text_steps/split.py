"""Text splitting processing step"""

from typing import Literal

from pydantic import Field

from .base import TextProcessStep


class SplitStep(TextProcessStep):
    """Text splitting processing step"""

    method: Literal["split"] = "split"
    separator: str = Field(..., description="Separator character or string")
    max_splits: int | None = Field(None, description="Maximum number of splits")

    async def process(self, input_data: str, step_id: str) -> list[str]:
        """Split text using specified separator"""
        if self.max_splits is not None:
            return input_data.split(self.separator, self.max_splits)
        return input_data.split(self.separator)
