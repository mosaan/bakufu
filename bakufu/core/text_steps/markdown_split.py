"""Markdown splitting text processing step"""

from typing import Any, Literal

from pydantic import Field

from ..step_registry import step_type
from .base import TextProcessStep


@step_type("text_process", "markdown_split")
class MarkdownSplitStep(TextProcessStep):
    """Markdown splitting text processing step"""

    method: Literal["markdown_split"] = "markdown_split"

    # Enhanced parameters
    split_type: Literal["section", "paragraph", "sentence"] = Field(
        "section", description="Split type"
    )
    header_level: int | None = Field(
        None, ge=1, le=6, description="Header level for section splits"
    )
    preserve_metadata: bool = Field(True, description="Preserve section metadata")

    async def process(self, input_data: str, step_id: str) -> list[dict[str, Any]]:
        """Split markdown based on split_type"""

        from ..exceptions import ErrorContext, StepExecutionError

        if self.split_type == "section":
            return await self._split_by_sections(input_data)
        elif self.split_type == "paragraph":
            return await self._split_by_paragraphs(input_data)
        elif self.split_type == "sentence":
            return await self._split_by_sentences(input_data)
        else:
            raise StepExecutionError(
                message=f"Unknown split_type: {self.split_type}",
                step_id=step_id,
                context=ErrorContext(step_id=step_id, function_name="MarkdownSplitStep.process"),
                suggestions=["Use one of: section, paragraph, sentence"],
            )

    async def _split_by_sections(self, input_data: str) -> list[dict[str, Any]]:
        """Split markdown into sections by headers"""
        import re

        sections: list[dict[str, Any]] = []
        current_section: dict[str, Any] = {"title": "", "content": "", "level": 0}

        # Check legacy behavior
        use_legacy_behavior = self.split_type == "section" and self.header_level is None

        lines = input_data.split("\n")
        for line in lines:
            # Check for markdown headers (# ## ### etc.)
            header_match = re.match(r"^(#{1,6})\s*(.*)", line.strip())
            if header_match:
                level = len(header_match.group(1))
                title = header_match.group(2)

                # Filter by header level if specified
                if self.header_level and level > self.header_level:
                    current_section["content"] = str(current_section["content"]) + line + "\n"
                    continue

                # Save previous section if it has content
                if current_section["title"] or str(current_section["content"]).strip():
                    sections.append(current_section.copy())

                # Start new section
                if use_legacy_behavior:
                    current_section = {
                        "title": line.strip(),
                        "content": "",
                    }
                else:
                    current_section = {
                        "title": title,
                        "content": "",
                    }
                    if self.preserve_metadata:
                        current_section["level"] = level
                        current_section["raw_header"] = line.strip()
            else:
                current_section["content"] = str(current_section["content"]) + line + "\n"

        # Add final section
        if current_section["title"] or str(current_section["content"]).strip():
            sections.append(current_section.copy())
        elif not input_data.strip():
            return []

        # Clean up content
        for section in sections:
            section["content"] = str(section["content"]).strip()

        return sections

    async def _split_by_paragraphs(self, input_data: str) -> list[dict[str, Any]]:
        """Split text into paragraphs"""
        paragraphs: list[dict[str, Any]] = []
        chunks = input_data.split("\n\n")

        for i, chunk in enumerate(chunks):
            chunk = chunk.strip()
            if chunk:
                paragraph: dict[str, Any] = {"content": chunk}
                if self.preserve_metadata:
                    paragraph["index"] = i
                    paragraph["word_count"] = len(chunk.split())
                paragraphs.append(paragraph)

        return paragraphs

    async def _split_by_sentences(self, input_data: str) -> list[dict[str, Any]]:
        """Split text into sentences"""
        import re

        sentences: list[dict[str, Any]] = []
        # Simple sentence splitting
        normalized_text = re.sub(r"([.!?])(?!\s|$)", r"\1 ", input_data)

        # Split on sentence-ending punctuation followed by whitespace
        sentence_pattern = r"([.!?]+)\s+"
        parts = re.split(sentence_pattern, normalized_text)

        # Reconstruct sentences
        current_sentence = ""
        sentence_index = 0

        for part in parts:
            if re.match(r"[.!?]+", part):
                if current_sentence.strip():
                    sent_dict: dict[str, Any] = {"content": current_sentence.strip()}
                    if self.preserve_metadata:
                        sent_dict["index"] = sentence_index
                        sent_dict["word_count"] = len(current_sentence.strip().split())
                        sent_dict["char_count"] = len(current_sentence.strip())
                    sentences.append(sent_dict)
                    sentence_index += 1
                current_sentence = ""
            else:
                current_sentence += part

        # Handle the last sentence
        if current_sentence.strip():
            clean_content = re.sub(r"[.!?]+$", "", current_sentence.strip())
            if clean_content:
                final_sent_dict: dict[str, Any] = {"content": clean_content}
                if self.preserve_metadata:
                    final_sent_dict["index"] = sentence_index
                    final_sent_dict["word_count"] = len(clean_content.split())
                    final_sent_dict["char_count"] = len(clean_content)
                sentences.append(final_sent_dict)

        return sentences
