from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Token:
    """A single lexical token produced by the NanoCalc lexer."""

    type: str
    value: str
    line: int
    column: int

    def __repr__(self) -> str:  # helpful for debugging
        return f"Token(type={self.type!r}, value={self.value!r}, line={self.line}, column={self.column})"
