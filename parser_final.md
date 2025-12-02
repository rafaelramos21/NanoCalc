# Parser da Linguagem NanoCalc — Implementação Final

Este documento entrega o **parser completo** inspirado no material do professor Moacyr, integrando:

- Estrutura LL(1) usando *recursive descent*  
- Integração total com o analisador léxico (Lexer)  
- Tratamento de erros sintáticos  
- Uma função para cada não-terminal  
- Compatível com o estudo de caso do link:  
  http://www.moacyrfc.com.br/clfa/temas/09/09_material_10_estudo_caso.html  

---

# 1. Estrutura Geral

O parser mantém:

- Um token de **lookahead**  
- Funções como `parse_program`, `parse_statement`, `parse_expr`  
- `_eat(tipo)` para consumir tokens esperados  
- Erros sintáticos com linha e coluna  

---

# 2. Gramática LL(1) adaptada de NanoCalc

```
program        → { statement }

statement      → letDecl
               | fnDecl
               | ifStmt
               | whileStmt
               | forStmt
               | idStatement
               | exprStmt

letDecl        → "let" ID "=" expr

fnDecl         → "fn" ID "(" paramList? ")" block
paramList      → ID ("," ID)*

block          → "{" { statement } "}"

ifStmt         → "if" "(" expr ")" block ("else" block)?

whileStmt      → "while" "(" expr ")" block

forStmt        → "for" "(" forInit ";" expr ";" expr ")" block
forInit        → "let" ID "=" expr
               | ID "=" expr
               | ε

idStatement    → ID idTail
idTail         → "=" expr
               | callSuffix
               | ε

callSuffix     → "(" argList? ")"
argList        → expr ("," expr)*

exprStmt       → expr
```

As expressões seguem o modelo descendente clássico (OR, AND, comparação, termos, fatores, unários, primários).

---

# 3. Implementação Completa do Parser

```python
# src/parser/parser.py

from lexer.lexer import Lexer
from lexer.token import Token


class ParserError(Exception):
    pass


class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.lookahead: Token = self.lexer.next_token()

    # =============================
    # Utilitário: consumir tokens
    # =============================
    def _eat(self, expected_type: str):
        if self.lookahead.type == expected_type:
            self.lookahead = self.lexer.next_token()
        else:
            raise ParserError(
                f"Erro sintático: esperado {expected_type}, encontrado {self.lookahead.type} "
                f"na linha {self.lookahead.line}, coluna {self.lookahead.column}"
            )

    # =============================
    # program ::= { statement }
    # =============================
    def parse_program(self):
        while self.lookahead.type != "EOF":
            self.parse_statement()
        return True

    # =============================
    # statement
    # =============================
    def parse_statement(self):
        t = self.lookahead.type

        if t == "KW_LET":
            return self.parse_let()
        elif t == "KW_FN":
            return self.parse_fn()
        elif t == "KW_IF":
            return self.parse_if()
        elif t == "KW_WHILE":
            return self.parse_while()
        elif t == "KW_FOR":
            return self.parse_for()
        elif t == "ID":
            return self.parse_idStatement()
        else:
            return self.parse_exprStmt()

    # letDecl
    def parse_let(self):
        self._eat("KW_LET")
        self._eat("ID")
        self._eat("ASSIGN")
        self.parse_expr()

    # idStatement ::= ID idTail
    def parse_idStatement(self):
        self._eat("ID")

        if self.lookahead.type == "ASSIGN":
            self._eat("ASSIGN")
            self.parse_expr()
        elif self.lookahead.type == "LPAREN":
            self.parse_callSuffix()
        # ε → nada

    def parse_callSuffix(self):
        self._eat("LPAREN")
        if self.lookahead.type != "RPAREN":
            self.parse_argList()
        self._eat("RPAREN")

    def parse_argList(self):
        self.parse_expr()
        while self.lookahead.type == "COMMA":
            self._eat("COMMA")
            self.parse_expr()

    def parse_exprStmt(self):
        self.parse_expr()

    # fnDecl
    def parse_fn(self):
        self._eat("KW_FN")
        self._eat("ID")
        self._eat("LPAREN")
        if self.lookahead.type == "ID":
            self.parse_paramList()
        self._eat("RPAREN")
        self.parse_block()

    def parse_paramList(self):
        self._eat("ID")
        while self.lookahead.type == "COMMA":
            self._eat("COMMA")
            self._eat("ID")

    # block
    def parse_block(self):
        self._eat("LBRACE")
        while self.lookahead.type != "RBRACE":
            self.parse_statement()
        self._eat("RBRACE")

    # if
    def parse_if(self):
        self._eat("KW_IF")
        self._eat("LPAREN")
        self.parse_expr()
        self._eat("RPAREN")
        self.parse_block()
        if self.lookahead.type == "KW_ELSE":
            self._eat("KW_ELSE")
            self.parse_block()

    # while
    def parse_while(self):
        self._eat("KW_WHILE")
        self._eat("LPAREN")
        self.parse_expr()
        self._eat("RPAREN")
        self.parse_block()

    # for
    def parse_for(self):
        self._eat("KW_FOR")
        self._eat("LPAREN")
        self.parse_forInit()
        self._eat("SEMICOLON")
        self.parse_expr()
        self._eat("SEMICOLON")
        self.parse_expr()
        self._eat("RPAREN")
        self.parse_block()

    def parse_forInit(self):
        if self.lookahead.type == "KW_LET":
            self._eat("KW_LET")
            self._eat("ID")
            self._eat("ASSIGN")
            self.parse_expr()
        elif self.lookahead.type == "ID":
            self._eat("ID")
            self._eat("ASSIGN")
            self.parse_expr()
        # ε

    # ========================================
    # Expressões
    # ========================================
    def parse_expr(self):
        self.parse_logic_or()

    def parse_logic_or(self):
        self.parse_logic_and()
        while self.lookahead.type == "OR":
            self._eat("OR")
            self.parse_logic_and()

    def parse_logic_and(self):
        self.parse_equality()
        while self.lookahead.type == "AND":
            self._eat("AND")
            self.parse_equality()

    def parse_equality(self):
        self.parse_comparison()
        while self.lookahead.type in ("EQ", "NEQ"):
            self._eat(self.lookahead.type)
            self.parse_comparison()

    def parse_comparison(self):
        self.parse_term()
        while self.lookahead.type in ("LT", "LE", "GT", "GE"):
            self._eat(self.lookahead.type)
            self.parse_term()

    def parse_term(self):
        self.parse_factor()
        while self.lookahead.type in ("PLUS", "MINUS"):
            self._eat(self.lookahead.type)
            self.parse_factor()

    def parse_factor(self):
        self.parse_power()
        while self.lookahead.type in ("MUL", "DIV", "MOD"):
            self._eat(self.lookahead.type)
            self.parse_power()

    def parse_power(self):
        self.parse_unary()
        while self.lookahead.type == "POW":
            self._eat("POW")
            self.parse_unary()

    def parse_unary(self):
        if self.lookahead.type in ("MINUS", "NOT"):
            self._eat(self.lookahead.type)
            self.parse_unary()
        else:
            self.parse_primary()

    def parse_primary(self):
        t = self.lookahead.type

        if t == "NUMBER":
            self._eat("NUMBER")
        elif t == "STRING":
            self._eat("STRING")
        elif t in ("KW_TRUE", "KW_FALSE"):
            self._eat(t)
        elif t == "ID":
            self._eat("ID")
            if self.lookahead.type == "LPAREN":
                self.parse_callSuffix()
        elif t == "LPAREN":
            self._eat("LPAREN")
            self.parse_expr()
            self._eat("RPAREN")
        elif t == "LBRACKET":
            self.parse_listMatrix()
        else:
            raise ParserError(f"Expressão inválida em {self.lookahead.line}:{self.lookahead.column}")

    def parse_listMatrix(self):
        self._eat("LBRACKET")
        self.parse_expr()
        while self.lookahead.type == "COMMA":
            self._eat("COMMA")
            self.parse_expr()
        self._eat("RBRACKET")
```

---

# 4. Como usar

```python
from lexer.buffer import InputBuffer
from lexer.lexer import Lexer
from parser.parser import Parser

code = open("program.nano").read()

lexer = Lexer(InputBuffer(code), afd)  # AFD gerado do AFN
parser = Parser(lexer)

parser.parse_program()
print("Programa sintaticamente correto!")
```

---

# 5. Entrega

Após subir este parser no repositório, envie:

```
https://github.com/SEU_USUARIO/NanoCalc/commit/SEU_HASH_AQUI
```

---

# Fim do documento.
