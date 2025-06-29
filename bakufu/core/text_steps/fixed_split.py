"""Fixed-size splitting text processing step"""

from typing import Any, Literal

from pydantic import Field

from .base import TextProcessStep


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
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(input_data):
            end = min(start + self.size, len(input_data))

            # Preserve word boundaries if requested
            if self.preserve_boundaries and end < len(input_data):
                # Find the last space before the boundary
                boundary_end = end
                while boundary_end > start and input_data[boundary_end] != " ":
                    boundary_end -= 1

                # If we found a space and it's not too close to start, use it
                if boundary_end > start and (end - boundary_end) <= self.size * 0.1:
                    end = boundary_end

            chunk_text = input_data[start:end].strip()
            if chunk_text:
                chunk = {
                    "content": chunk_text,
                    "index": chunk_index,
                    "start_pos": start,
                    "end_pos": end,
                    "char_count": len(chunk_text),
                    "word_count": len(chunk_text.split()),
                }
                chunks.append(chunk)
                chunk_index += 1

            # Move start position with overlap consideration
            if self.overlap > 0:
                next_start = start + self.size - self.overlap
                if next_start >= len(input_data):
                    break
                start = next_start
            else:
                start = end

        return chunks

    async def _split_by_tokens(self, input_data: str) -> list[dict[str, Any]]:
        """Split text by token count (approximated by words)"""
        words = input_data.split()
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(words):
            end = min(start + self.size, len(words))

            chunk_words = words[start:end]
            chunk_text = " ".join(chunk_words)

            if chunk_text:
                chunk = {
                    "content": chunk_text,
                    "index": chunk_index,
                    "start_token": start,
                    "end_token": end,
                    "token_count": len(chunk_words),
                    "char_count": len(chunk_text),
                }
                chunks.append(chunk)
                chunk_index += 1

            # Move start position with overlap consideration
            start = max(start + self.size - self.overlap, end)

            # Prevent infinite loop
            if start <= end - self.size + self.overlap:
                start = end

        return chunks
