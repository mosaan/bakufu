"""Text splitting processing step"""

from typing import Literal

from pydantic import Field

from .base import TextProcessStep


class SplitStep(TextProcessStep):
    """Text splitting processing step"""

    method: Literal["split"] = "split"
    separator: str = Field(..., description="Separator character or string")
    max_splits: int | None = Field(None, description="Maximum number of splits")
    preserve_empty: bool = Field(False, description="Whether to preserve empty parts")

    async def process(self, input_data: str, step_id: str) -> list[str]:
        """Split text using specified separator"""
        max_splits = self.max_splits if self.max_splits is not None else -1

        parts = input_data.split(self.separator, max_splits)
        if not self.preserve_empty:
            # Filter out empty parts, but preserve single empty string result from empty input
            filtered_parts = [part for part in parts if part.strip()]
            # If we filtered everything out but original had content, return empty list
            # If original was empty, preserve the single empty string
            if not filtered_parts and parts == [""]:
                return [""]
            return filtered_parts
        return parts

    @staticmethod
    def split_fixed_size(
        text: str, size: int, unit: Literal["characters", "words"] = "characters", overlap: int = 0
    ) -> list[str]:
        """Split text into fixed-size chunks"""
        if unit == "characters":
            return SplitStep._split_by_characters(text, size, overlap)
        elif unit == "words":
            return SplitStep._split_by_words(text, size, overlap)
        else:
            raise ValueError(f"Unsupported unit: {unit}")

    @staticmethod
    def _split_by_characters(text: str, size: int, overlap: int = 0) -> list[str]:
        """Split text by character count"""
        if size <= 0:
            raise ValueError("Size must be positive")
        if overlap >= size:
            raise ValueError("Overlap must be less than size")

        chunks = []
        start = 0

        while start < len(text):
            end = start + size
            chunk = text[start:end]

            # Only add if we have a meaningful chunk
            if chunk:
                chunks.append(chunk)

            if end >= len(text):
                break

            # Calculate next start position with overlap
            next_start = end - overlap

            # If next start would create a chunk that's too short and overlaps significantly,
            # try to adjust to get a fuller chunk
            if len(text) - next_start < size and len(text) - next_start > 0:
                # If remaining text is shorter than size but we have room to start earlier
                # to get a full-size chunk, do that
                potential_start = len(text) - size
                if potential_start > start and potential_start >= next_start - overlap:
                    start = potential_start
                else:
                    start = next_start
            else:
                start = next_start

        return chunks

    @staticmethod
    def _split_by_words(text: str, size: int, overlap: int = 0) -> list[str]:
        """Split text by word count"""
        if size <= 0:
            raise ValueError("Size must be positive")
        if overlap >= size:
            raise ValueError("Overlap must be less than size")

        words = text.split()
        chunks = []
        start = 0

        while start < len(words):
            end = start + size
            chunk_words = words[start:end]
            chunks.append(" ".join(chunk_words))

            if end >= len(words):
                break

            start = end - overlap

        return chunks
