"""Fixed-size splitting text processing step"""

from typing import Any, Literal

from pydantic import Field

from ..step_registry import step_type
from .base import TextProcessStep
from .split import SplitStep


@step_type("text_process", "fixed_split")
class FixedSplitStep(TextProcessStep):
    """Fixed-size splitting text processing step"""

    method: Literal["fixed_split"] = "fixed_split"

    split_by: Literal["tokens", "characters"] = Field(
        "characters", description="Split by tokens or characters"
    )
    size: int = Field(..., gt=0, description="Split size")
    overlap: int = Field(0, ge=0, description="Overlap size")
    preserve_boundaries: bool = Field(True, description="Preserve word boundaries")

    async def process(self, input_data: str, step_id: str) -> list[dict[str, Any]]:
        """Split text into fixed-size chunks"""
        from ..exceptions import ErrorContext, StepExecutionError

        if self.split_by == "characters":
            return await self._split_by_characters(input_data)
        elif self.split_by == "tokens":
            return await self._split_by_tokens(input_data)
        else:
            raise StepExecutionError(
                message=f"Unknown split_by: {self.split_by}",
                step_id=step_id,
                context=ErrorContext(step_id=step_id, function_name="FixedSplitStep.process"),
                suggestions=["Use 'characters' or 'tokens'"],
            )

    async def _split_by_characters(self, input_data: str) -> list[dict[str, Any]]:
        """Split text by character count"""
        # Manual chunking to track positions correctly
        chunks = []
        start = 0

        chunk_index = 0
        while start < len(input_data):
            end = start + self.size
            chunk_text = input_data[start:end]

            # Apply boundary preservation if requested
            if self.preserve_boundaries and end < len(input_data):
                # Find the last space before the boundary
                boundary_end = end
                while boundary_end > start and input_data[boundary_end] != " ":
                    boundary_end -= 1

                # If we found a space and it's not too close to start, use it
                if boundary_end > start and (end - boundary_end) <= self.size * 0.1:
                    end = boundary_end
                    chunk_text = input_data[start:end]

            if chunk_text.strip():
                chunk = {
                    "content": chunk_text.strip(),
                    "index": chunk_index,
                    "start_pos": start,
                    "end_pos": end,
                    "char_count": len(chunk_text.strip()),
                    "word_count": len(chunk_text.strip().split()),
                }
                chunks.append(chunk)
                chunk_index += 1

            if end >= len(input_data):
                break

            # Calculate next start position with overlap
            next_start = end - self.overlap

            # Handle case where remaining text is shorter than size
            if len(input_data) - next_start < self.size and len(input_data) - next_start > 0:
                potential_start = len(input_data) - self.size
                if potential_start > start and potential_start >= next_start - self.overlap:
                    start = potential_start
                else:
                    start = next_start
            else:
                start = next_start

        return chunks

    async def _split_by_tokens(self, input_data: str) -> list[dict[str, Any]]:
        """Split text by token count (approximated by words)"""
        # Use common library for basic splitting
        raw_chunks = SplitStep.split_fixed_size(
            input_data, self.size, unit="words", overlap=self.overlap
        )

        # Add metadata
        chunks = []
        for chunk_index, chunk_text in enumerate(raw_chunks):
            if chunk_text.strip():
                chunk_words = chunk_text.split()
                chunk = {
                    "content": chunk_text.strip(),
                    "index": chunk_index,
                    "start_token": 0,  # Position tracking would require more complex logic
                    "end_token": len(chunk_words),
                    "token_count": len(chunk_words),
                    "char_count": len(chunk_text.strip()),
                }
                chunks.append(chunk)

        return chunks
