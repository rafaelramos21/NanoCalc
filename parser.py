from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..lexer.lexer import Lexer
from ..lexer.token import Token


class ParserError(Exception):
    pass


@dataclass
class ASTNode:
    """Tiny AST placeholder (enough to prove parsing works)."""
    kind: str
    value: Optional[str] = None
    left: Optional["ASTNode"] = None
    right: Optional["ASTNode"] = None


class Parser:
    """Recursive-descent parser for the LL(1) NanoCalc subset in docs/parser_final.md.

    This implementation focuses on correctness and helpful errors, and builds a small AST
    for expressions. For statements it returns nodes of kind 'Stmt' / 'Block' etc.
    """

    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.lookahead: Token = self.lexer.next_token()

    def _eat(self, expected_type: str) -> Token:
        if self.lookahead.type == expected_type:
            cur = self.lookahead
            self.lookahead = self.lexer.next_token()
            return cur
        raise ParserError(
            f"Erro sintático: esperado {expected_type}, encontrado {self.lookahead.type} "
            f"na linha {self.lookahead.line}, coluna {self.lookahead.column}"
        )

    def _accept(self, token_type: str) -> Optional[Token]:
        if self.lookahead.type == token_type:
            return self._eat(token_type)
        return None

    # program → { statement }
    def parse_program(self) -> ASTNode:
        stmts = []
        while self.lookahead.type != "EOF":
            stmts.append(self.parse_statement())
        return ASTNode("Program", left=None, right=None, value=str(len(stmts)))

    # statement dispatch
    def parse_statement(self) -> ASTNode:
        t = self.lookahead.type
        if t == "KW_LET":
            return self.parse_let()
        if t == "KW_FN":
            return self.parse_fn()
        if t == "KW_IF":
            return self.parse_if()
        if t == "KW_WHILE":
            return self.parse_while()
        if t == "KW_FOR":
            return self.parse_for()
        if t == "ID":
            # Could be assignment or call or expression statement
            # We'll try the idStatement path (as in docs)
            return self.parse_idStatement()
        return self.parse_exprStmt()

    # letDecl → "let" ID "=" expr
    def parse_let(self) -> ASTNode:
        self._eat("KW_LET")
        name = self._eat("ID")
        self._eat("ASSIGN")
        expr = self.parse_expr()
        self._accept("SEMICOLON")
        return ASTNode("Let", value=name.value, left=expr)

    # fnDecl → "fn" ID "(" paramList? ")" block
    def parse_fn(self) -> ASTNode:
        self._eat("KW_FN")
        name = self._eat("ID")
        self._eat("LPAREN")
        # paramList? → ID ("," ID)*
        if self.lookahead.type == "ID":
            self._eat("ID")
            while self._accept("COMMA"):
                self._eat("ID")
        self._eat("RPAREN")
        block = self.parse_block()
        return ASTNode("Fn", value=name.value, left=block)

    # block → "{" { statement } "}"
    def parse_block(self) -> ASTNode:
        self._eat("LBRACE")
        count = 0
        while self.lookahead.type != "RBRACE":
            # basic protection against EOF
            if self.lookahead.type == "EOF":
                raise ParserError(
                    f"Erro sintático: bloco não terminado (esperado '}}') "
                    f"na linha {self.lookahead.line}, coluna {self.lookahead.column}"
                )
            self.parse_statement()
            count += 1
        self._eat("RBRACE")
        return ASTNode("Block", value=str(count))

    # ifStmt → "if" "(" expr ")" block ("else" block)?
    def parse_if(self) -> ASTNode:
        self._eat("KW_IF")
        self._eat("LPAREN")
        cond = self.parse_expr()
        self._eat("RPAREN")
        then_block = self.parse_block()
        else_block = None
        if self._accept("KW_ELSE"):
            else_block = self.parse_block()
        return ASTNode("If", left=cond, right=then_block, value=("else" if else_block else None))

    # whileStmt → "while" "(" expr ")" block
    def parse_while(self) -> ASTNode:
        self._eat("KW_WHILE")
        self._eat("LPAREN")
        self.parse_expr()
        self._eat("RPAREN")
        self.parse_block()
        return ASTNode("While")

    # forStmt → "for" "(" forInit ";" expr ";" expr ")" block
    def parse_for(self) -> ASTNode:
        self._eat("KW_FOR")
        self._eat("LPAREN")
        self.parse_forInit()
        self._eat("SEMICOLON")
        self.parse_expr()
        self._eat("SEMICOLON")
        self.parse_expr()
        self._eat("RPAREN")
        self.parse_block()
        return ASTNode("For")

    # forInit → "let" ID "=" expr | ID "=" expr | ε
    def parse_forInit(self) -> None:
        if self.lookahead.type == "KW_LET":
            self._eat("KW_LET")
            self._eat("ID")
            self._eat("ASSIGN")
            self.parse_expr()
            return
        if self.lookahead.type == "ID":
            # look ahead for assignment
            self._eat("ID")
            if self._accept("ASSIGN"):
                self.parse_expr()
            return
        # ε (empty)

    # idStatement → ID idTail
    # idTail → "=" expr | callSuffix | ε
    def parse_idStatement(self) -> ASTNode:
        ident = self._eat("ID")
        if self._accept("ASSIGN"):
            expr = self.parse_expr()
            self._accept("SEMICOLON")
            return ASTNode("Assign", value=ident.value, left=expr)
        if self.lookahead.type == "LPAREN":
            self.parse_callSuffix()
            self._accept("SEMICOLON")
            return ASTNode("CallStmt", value=ident.value)
        # ε -> treat as expression statement (just the identifier)
        self._accept("SEMICOLON")
        return ASTNode("ExprStmt", left=ASTNode("Id", value=ident.value))

    # callSuffix → "(" argList? ")"
    def parse_callSuffix(self) -> None:
        self._eat("LPAREN")
        if self.lookahead.type != "RPAREN":
            self.parse_argList()
        self._eat("RPAREN")

    # argList → expr ("," expr)*
    def parse_argList(self) -> None:
        self.parse_expr()
        while self._accept("COMMA"):
            self.parse_expr()

    # exprStmt → expr
    def parse_exprStmt(self) -> ASTNode:
        expr = self.parse_expr()
        self._accept("SEMICOLON")
        return ASTNode("ExprStmt", left=expr)

    # =============================
    # Expressions (classic precedence)
    # =============================
    def parse_expr(self) -> ASTNode:
        return self.parse_or()

    def parse_or(self) -> ASTNode:
        node = self.parse_and()
        while self._accept("OR"):
            rhs = self.parse_and()
            node = ASTNode("Or", left=node, right=rhs)
        return node

    def parse_and(self) -> ASTNode:
        node = self.parse_equality()
        while self._accept("AND"):
            rhs = self.parse_equality()
            node = ASTNode("And", left=node, right=rhs)
        return node

    def parse_equality(self) -> ASTNode:
        node = self.parse_comparison()
        while self.lookahead.type in ("EQ", "NEQ"):
            op = self.lookahead.type
            self._eat(op)
            rhs = self.parse_comparison()
            node = ASTNode(op, left=node, right=rhs)
        return node

    def parse_comparison(self) -> ASTNode:
        node = self.parse_term()
        while self.lookahead.type in ("LT", "LE", "GT", "GE"):
            op = self.lookahead.type
            self._eat(op)
            rhs = self.parse_term()
            node = ASTNode(op, left=node, right=rhs)
        return node

    def parse_term(self) -> ASTNode:
        node = self.parse_factor()
        while self.lookahead.type in ("PLUS", "MINUS"):
            op = self.lookahead.type
            self._eat(op)
            rhs = self.parse_factor()
            node = ASTNode(op, left=node, right=rhs)
        return node

    def parse_factor(self) -> ASTNode:
        node = self.parse_unary()
        while self.lookahead.type in ("MULTIPLY", "DIVIDE", "MOD"):
            op = self.lookahead.type
            self._eat(op)
            rhs = self.parse_unary()
            node = ASTNode(op, left=node, right=rhs)
        return node

    def parse_unary(self) -> ASTNode:
        if self.lookahead.type in ("NOT", "MINUS", "PLUS"):
            op = self.lookahead.type
            self._eat(op)
            rhs = self.parse_unary()
            return ASTNode("Unary" + op, left=rhs)
        return self.parse_primary()

    def parse_primary(self) -> ASTNode:
        if self.lookahead.type == "NUMBER":
            t = self._eat("NUMBER")
            return ASTNode("Number", value=t.value)
        if self.lookahead.type == "STRING":
            t = self._eat("STRING")
            return ASTNode("String", value=t.value)
        if self.lookahead.type in ("KW_TRUE", "KW_FALSE"):
            t = self._eat(self.lookahead.type)
            return ASTNode("Bool", value=t.value)
        if self.lookahead.type == "ID":
            ident = self._eat("ID")
            # call?
            if self.lookahead.type == "LPAREN":
                self.parse_callSuffix()
                return ASTNode("Call", value=ident.value)
            return ASTNode("Id", value=ident.value)
        if self._accept("LPAREN"):
            node = self.parse_expr()
            self._eat("RPAREN")
            return node
        raise ParserError(
            f"Erro sintático: expressão inválida perto de {self.lookahead.type} "
            f"na linha {self.lookahead.line}, coluna {self.lookahead.column}"
        )
