from __future__ import annotations

import re
from typing import Iterator, Optional

from .buffer import InputBuffer
from .token import Token


class LexerError(Exception):
    """Raised when the lexer finds an invalid or malformed token."""


KEYWORDS = {
    "let": "KW_LET",
    "fn": "KW_FN",
    "return": "KW_RETURN",
    "if": "KW_IF",
    "else": "KW_ELSE",
    "for": "KW_FOR",
    "while": "KW_WHILE",
    "in": "KW_IN",
    "true": "KW_TRUE",
    "false": "KW_FALSE",
}

# Regex parts (kept close to docs/especificacao_lexica.md)
_RE_WHITESPACE = re.compile(r"[\t\f\r\n ]+")
_RE_COMMENT_LINE = re.compile(r"#[^\n]*")
_RE_COMMENT_BLOCK = re.compile(r"/\*[^*]*\*+(?:[^/*][^*]*\*+)*/", re.DOTALL)

# Strings: single or double quotes, no literal newlines, allow escapes like \n, \t, \\, \", \'
_RE_STRING = re.compile(r"'(?:[^\\'\n]|\\.)*'|\"(?:[^\\\"\n]|\\.)*\"")

# Numbers:
# INT: [0-9]+
# DEC: (?:[0-9]+\.[0-9]*|\.[0-9]+)
# SCI: (?: (?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+) [eE] [+-]? [0-9]+ )
_RE_NUMBER = re.compile(
    r"(?:"
    r"(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)[eE][+-]?[0-9]+"
    r"|(?:[0-9]+\.[0-9]*|\.[0-9]+)"
    r"|[0-9]+"
    r")"
)

_RE_ID = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# Operators and delimiters (maximal munch)
OPERATORS_2 = {
    "==": "EQ",
    "!=": "NEQ",
    "<=": "LE",
    ">=": "GE",
    "&&": "AND",
    "||": "OR",
}
OPERATORS_1 = {
    "+": "PLUS",
    "-": "MINUS",
    "*": "MULTIPLY",
    "/": "DIVIDE",
    "^": "POW",
    "%": "MOD",
    "=": "ASSIGN",
    "<": "LT",
    ">": "GT",
    "!": "NOT",
}

DELIMS = {
    "(": "LPAREN",
    ")": "RPAREN",
    "[": "LBRACKET",
    "]": "RBRACKET",
    "{": "LBRACE",
    "}": "RBRACE",
    ",": "COMMA",
    ":": "COLON",
    ";": "SEMICOLON",
}


class Lexer:
    """NanoCalc lexer (regex-based with maximal munch & good errors).

    Produces Token objects with line/column.
    """

    def __init__(self, buffer: InputBuffer):
        self.buf = buffer
        self.line = 1
        self.col = 1

    def _advance(self, text: str) -> None:
        """Advance cursor and keep line/column consistent."""
        for ch in text:
            if ch == "\n":
                self.line += 1
                self.col = 1
            else:
                self.col += 1
        self.buf.advance(len(text))

    def _match(self, regex: re.Pattern[str]) -> Optional[str]:
        m = regex.match(self.buf.remaining())
        return m.group(0) if m else None

    def next_token(self) -> Token:
        # Skip whitespace/comments repeatedly
        while not self.buf.eof():
            start_line, start_col = self.line, self.col
            rem = self.buf.remaining()

            # Whitespace
            ws = self._match(_RE_WHITESPACE)
            if ws:
                self._advance(ws)
                continue

            # Line comment
            lc = self._match(_RE_COMMENT_LINE)
            if lc:
                self._advance(lc)
                continue

            # Block comment (must be closed)
            if rem.startswith("/*"):
                bc = self._match(_RE_COMMENT_BLOCK)
                if bc:
                    self._advance(bc)
                    continue
                raise LexerError(
                    f"Erro léxico na linha {start_line}, coluna {start_col}: comentário de bloco não terminado"
                )

            # String (must be closed)
            if rem.startswith(("'", '"')):
                s = self._match(_RE_STRING)
                if s:
                    tok = Token("STRING", s, start_line, start_col)
                    self._advance(s)
                    return tok
                raise LexerError(f"Erro léxico na linha {start_line}, coluna {start_col}: string não terminada")

            # Operators (2 chars first)
            two = rem[:2]
            if two in OPERATORS_2:
                tok = Token(OPERATORS_2[two], two, start_line, start_col)
                self._advance(two)
                return tok

            one = rem[:1]
            if one in OPERATORS_1:
                tok = Token(OPERATORS_1[one], one, start_line, start_col)
                self._advance(one)
                return tok

            if one in DELIMS:
                tok = Token(DELIMS[one], one, start_line, start_col)
                self._advance(one)
                return tok

            # Number (note: '.' only valid when part of DEC/SCI by regex)
            num = self._match(_RE_NUMBER)
            if num:
                tok = Token("NUMBER", num, start_line, start_col)
                self._advance(num)
                return tok

            # Identifier / Keyword
            ident = self._match(_RE_ID)
            if ident:
                ttype = KEYWORDS.get(ident, "ID")
                tok = Token(ttype, ident, start_line, start_col)
                self._advance(ident)
                return tok

            bad = rem[0]
            raise LexerError(f"Erro léxico na linha {start_line}, coluna {start_col}: caractere inválido {bad!r}")

        return Token("EOF", "", self.line, self.col)

    def tokenize(self) -> Iterator[Token]:
        while True:
            t = self.next_token()
            yield t
            if t.type == "EOF":
                break
