from __future__ import annotations


class InputBuffer:
    """A minimal input buffer with a cursor."""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0

    def eof(self) -> bool:
        return self.pos >= len(self.text)

    def peek(self, n: int = 1) -> str:
        """Return the next n characters without consuming them."""
        if self.eof():
            return ""
        return self.text[self.pos : self.pos + n]

    def advance(self, n: int = 1) -> str:
        """Consume and return the next n characters."""
        if n <= 0:
            return ""
        start = self.pos
        self.pos = min(len(self.text), self.pos + n)
        return self.text[start : self.pos]

    def remaining(self) -> str:
        return self.text[self.pos :]

    def __len__(self) -> int:
        return len(self.text)
