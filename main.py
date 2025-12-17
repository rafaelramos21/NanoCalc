from __future__ import annotations

import argparse
from pathlib import Path

from .lexer.buffer import InputBuffer
from .lexer.lexer import Lexer, LexerError
from .parser.parser import Parser, ParserError


def run_lex(path: Path) -> int:
    source = path.read_text(encoding="utf-8")
    lexer = Lexer(InputBuffer(source))
    print(f"{'TYPE':<12} {'VALUE':<20} @ (line,col)")
    print("-" * 60)
    try:
        for tok in lexer.tokenize():
            print(f"{tok.type:<12} {tok.value!s:<20} @ ({tok.line},{tok.column})")
    except LexerError as e:
        print(str(e))
        return 1
    return 0


def run_parse(path: Path) -> int:
    source = path.read_text(encoding="utf-8")
    lexer = Lexer(InputBuffer(source))
    parser = Parser(lexer)
    try:
        parser.parse_program()
        print("OK: parsing concluído (nenhum erro sintático encontrado).")
        return 0
    except (LexerError, ParserError) as e:
        print(str(e))
        return 1


def main() -> int:
    ap = argparse.ArgumentParser(prog="nanocalc", description="NanoCalc (lexer + parser) – versão mínima funcional.")
    ap.add_argument("file", type=Path, help="arquivo .nano/.nanocalc")
    ap.add_argument("--lex", action="store_true", help="apenas tokenizar (lexer)")
    args = ap.parse_args()

    if not args.file.exists():
        print(f"Arquivo não encontrado: {args.file}")
        return 1

    if args.lex:
        return run_lex(args.file)
    return run_parse(args.file)


if __name__ == "__main__":
    raise SystemExit(main())
