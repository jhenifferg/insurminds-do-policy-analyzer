"""Conservative structural normalization for extracted text."""

import re


class TextCleaner:
    """Normalize text whitespace without changing its semantic content."""

    def clean(self, text: str) -> str:
        """Return a deterministically normalized representation of ``text``."""
        if text == "":
            return ""

        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in normalized.split("\n")]
        normalized = "\n".join(lines)
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)
        return normalized.strip()
