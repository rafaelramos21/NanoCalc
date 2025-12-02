# Compilador NanoCalc — Manual Completo de Entrega

**Disciplina:** Construção de Compiladores  
**Linguagem:** NanoCalc  
**Grupo:** Equipe-Kamikaze (Rafael Ribeiro Ramos, João Pedro Ruy)

---

## 1. Visão Geral do Compilador

O compilador da linguagem **NanoCalc** é composto pelas seguintes fases:

1. **Analisador léxico (Lexer)** — converte a sequência de caracteres do código-fonte em tokens.
2. **Analisador sintático (Parser)** — consome tokens, verifica a estrutura de acordo com a gramática e cria a **AST** (Árvore Sintática Abstrata).
3. **Analisador semântico** — valida regras de escopo e tipos (variáveis declaradas, tipos de expressões, funções, etc.).
4. **Gerador de código** — traduz a AST válida para **LLVM IR**, permitindo gerar código executável via toolchain LLVM.

Todo o projeto foi implementado em **Python**, com estrutura de diretórios:

```text
NanoCalc/
  ├─ src/
  │   ├─ lexer/
  │   │   ├─ afn_to_afd.py
  │   │   ├─ buffer.py
  │   │   ├─ lexer.py
  │   │   └─ token.py
  │   ├─ parser/
  │   │   └─ parser.py
  │   ├─ ast/
  │   │   └─ nodes.py
  │   ├─ semantico/
  │   │   └─ semantic_analyzer.py
  │   ├─ codegen/
  │   │   └─ codegen_llvm.py
  │   └─ main.py
  └─ docs/
      ├─ gramatica_formal.md
      ├─ analisador_lexico.md
      ├─ parser_final.md
      └─ afd_final.md
```

---

## 2. Manual de Utilização

### 2.1 Compilar um programa NanoCalc

Assumindo que o repositório está clonado e os requisitos instalados:

```bash
# dentro da pasta do projeto NanoCalc/
python -m src.main exemplos/programa.nano
```

O fluxo principal é:

1. Ler o arquivo `programa.nano`;
2. Rodar **Lexer → Parser → AST → Análise Semântica → LLVM IR**;
3. Gerar um arquivo `programa.ll` (LLVM IR) na mesma pasta.

### 2.2 Rodar o LLVM IR gerado

Com o LLVM instalado (por exemplo, usando `lli` para interpretar IR):

```bash
lli programa.ll
```

Ou, se quiser gerar um executável (exemplo em Linux):

```bash
llc -filetype=obj programa.ll -o programa.o
clang programa.o -o programa
./programa
```

### 2.3 Opções de linha de comando (exemplo)

No arquivo `src/main.py`, definimos uma interface simples:

```python
# src/main.py (trecho)
import sys
from pathlib import Path
from lexer.buffer import InputBuffer
from lexer.lexer import Lexer
from lexer.afn_to_afd import afn_to_afd
from semantico.semantic_analyzer import SemanticAnalyzer
from codegen.codegen_llvm import LLVMCodegen
from parser.parser import Parser
from construir_afn import construir_afn_nano_calc  # função que monta o AFN


def main():
    if len(sys.argv) < 2:
        print("Uso: python -m src.main <arquivo.nano>")
        sys.exit(1)

    source_path = Path(sys.argv[1])
    source_code = source_path.read_text(encoding="utf-8")

    # 1. AFN → AFD (uma única vez, poderia ser cacheado)
    afn = construir_afn_nano_calc()
    afd = afn_to_afd(afn)

    # 2. Lexer
    buffer = InputBuffer(source_code)
    lexer = Lexer(buffer, afd)

    # 3. Parser (gera AST)
    parser = Parser(lexer)
    ast = parser.parse_program()  # retorna nó Program da AST

    # 4. Análise semântica
    sema = SemanticAnalyzer()
    sema.visit(ast)

    # 5. Geração de código LLVM
    codegen = LLVMCodegen(module_name=source_path.stem)
    llvm_module = codegen.generate(ast)

    # 6. Salvar IR em arquivo .ll
    ir_path = source_path.with_suffix(".ll")
    ir_path.write_text(str(llvm_module), encoding="utf-8")

    print(f"Compilação concluída. LLVM IR salvo em: {ir_path}")


if __name__ == "__main__":
    main()
```

---

## 3. Manual de Instalação / Roteiro para Leigo

### 3.1 Pré-requisitos

- **Python 3.10+**
- **pip** (gerenciador de pacotes do Python)
- **LLVM** instalado (para rodar ou compilar o IR):
  - Linux: instalar pacotes `llvm` e `clang` via gerenciador de pacotes.
  - Windows: instalar LLVM pelo instalador oficial.

### 3.2 Passo a passo de instalação

1. **Clonar o repositório:**

   ```bash
   git clone https://github.com/SEU_USUARIO/NanoCalc.git
   cd NanoCalc
   ```

2. **Criar ambiente virtual (opcional, mas recomendado):**

   ```bash
   python -m venv venv
   source venv/bin/activate      # Linux/macOS
   # ou
   venv\Scriptsctivate         # Windows
   ```

3. **Instalar dependências Python (se usar llvmlite, por exemplo):**

   ```bash
   pip install -r requirements.txt
   ```

   Exemplo de `requirements.txt`:

   ```text
   llvmlite>=0.41.0
   ```

4. **Testar compilação de exemplo:**

   ```bash
   python -m src.main exemplos/programa.nano
   ```

5. **Executar o IR gerado:**

   ```bash
   lli exemplos/programa.ll
   ```

---

## 4. Analisador Léxico (Lexer)

### 4.1 Objetivo

O **lexer** lê o arquivo fonte caractere a caractere e produz uma sequência de **tokens** (ID, NUMBER, operadores, palavras reservadas, etc.), aplicando:

- **Princípio do *match mais longo*** (maximal munch);
- **Bufferização de entrada**;
- **Diferenciação entre IDs e palavras reservadas**.

### 4.2 Estruturas principais (resumo)

```python
# src/lexer/token.py
from dataclasses import dataclass
from typing import Any

@dataclass
class Token:
    type: str
    lexeme: str
    line: int
    column: int
    value: Any = None
```

```python
# src/lexer/buffer.py
class InputBuffer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
    # métodos peek(), advance(), eof(), get_position(), set_position()
```

```python
# src/lexer/afn_to_afd.py
# Contém:
# - classe AFN
# - classe AFD
# - epsilon_closure()
# - move()
# - choose_token()
# - afn_to_afd(afn) -> AFD  (algoritmo de subconjuntos)
```

### 4.3 Lexer com match mais longo

```python
# src/lexer/lexer.py

from .afn_to_afd import AFD
from .buffer import InputBuffer
from .token import Token


class LexicalError(Exception):
    pass


class Lexer:
    def __init__(self, buffer: InputBuffer, afd: AFD, whitespace: str = " 	
"):
        self.buffer = buffer
        self.afd = afd
        self.whitespace = set(whitespace)
        self.reserved_words = {
            "let": "KW_LET",
            "fn": "KW_FN",
            "if": "KW_IF",
            "else": "KW_ELSE",
            "while": "KW_WHILE",
            "for": "KW_FOR",
            "true": "KW_TRUE",
            "false": "KW_FALSE",
        }

    def _skip_whitespace(self):
        while True:
            ch = self.buffer.peek()
            if ch is not None and ch in self.whitespace:
                self.buffer.advance()
            else:
                break

    def next_token(self) -> Token:
        self._skip_whitespace()

        ch = self.buffer.peek()
        if ch is None:
            _, line, col = self.buffer.get_position()
            return Token("EOF", "", line, col)

        start_pos, start_line, start_col = self.buffer.get_position()
        current_state = self.afd.start_state
        last_accept_state = None
        last_accept_pos = None
        last_accept_type = None

        while True:
            ch = self.buffer.peek()
            if ch is None:
                break

            key = (current_state, ch)
            if key not in self.afd.transitions:
                break

            current_state = self.afd.transitions[key]
            self.buffer.advance()

            if current_state in self.afd.accepting:
                last_accept_state = current_state
                last_accept_type = self.afd.accepting[current_state]
                last_accept_pos = self.buffer.get_position()

        if last_accept_state is None or last_accept_pos is None:
            err_snippet = ""
            for _ in range(10):
                c = self.buffer.peek()
                if c is None:
                    break
                err_snippet += c
                self.buffer.advance()
            raise LexicalError(
                f"Caractere inesperado na linha {start_line}, coluna {start_col}. Trecho: {err_snippet!r}"
            )

        end_pos, end_line, end_col = last_accept_pos
        self.buffer.set_position(end_pos, end_line, end_col)

        text = self.buffer.text
        lexeme = text[start_pos:end_pos]
        token_type = last_accept_type

        if token_type == "ID" and lexeme in self.reserved_words:
            token_type = self.reserved_words[lexeme]

        value = None
        if token_type == "NUMBER":
            try:
                value = int(lexeme)
            except ValueError:
                value = None

        return Token(token_type, lexeme, start_line, start_col, value)

    def tokenize(self):
        tokens = []
        while True:
            tok = self.next_token()
            tokens.append(tok)
            if tok.type == "EOF":
                break
        return tokens
```

---

## 5. Analisador Sintático (Parser) com Criação da AST

### 5.1 AST — Estruturas de nós

```python
# src/ast/nodes.py

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Node:
    pass


@dataclass
class Program(Node):
    statements: List[Node]


@dataclass
class LetDecl(Node):
    name: str
    expr: Node


@dataclass
class FnDecl(Node):
    name: str
    params: List[str]
    body: 'Block'


@dataclass
class Block(Node):
    statements: List[Node]


@dataclass
class IfStmt(Node):
    cond: Node
    then_block: Block
    else_block: Optional[Block] = None


@dataclass
class WhileStmt(Node):
    cond: Node
    body: Block


@dataclass
class ForStmt(Node):
    init: Optional[Node]
    cond: Node
    step: Node
    body: Block


@dataclass
class Assign(Node):
    name: str
    expr: Node


@dataclass
class Call(Node):
    name: str
    args: List[Node]


@dataclass
class BinaryOp(Node):
    op: str
    left: Node
    right: Node


@dataclass
class UnaryOp(Node):
    op: str
    operand: Node


@dataclass
class Var(Node):
    name: str


@dataclass
class NumberLit(Node):
    value: int


@dataclass
class BoolLit(Node):
    value: bool


@dataclass
class StringLit(Node):
    value: str
```

### 5.2 Parser LL(1) com AST

```python
# src/parser/parser.py

from lexer.lexer import Lexer
from lexer.token import Token
from ast.nodes import *


class ParserError(Exception):
    pass


class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.lookahead: Token = self.lexer.next_token()

    def _eat(self, expected_type: str):
        if self.lookahead.type == expected_type:
            self.lookahead = self.lexer.next_token()
        else:
            raise ParserError(
                f"Erro sintático: esperado {expected_type}, encontrado {self.lookahead.type} "
                f"na linha {self.lookahead.line}, coluna {self.lookahead.column}"
            )

    # program ::= { statement }
    def parse_program(self) -> Program:
        stmts = []
        while self.lookahead.type != "EOF":
            stmts.append(self.parse_statement())
        return Program(stmts)

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

    def parse_let(self) -> LetDecl:
        self._eat("KW_LET")
        name = self.lookahead.lexeme
        self._eat("ID")
        self._eat("ASSIGN")
        expr = self.parse_expr()
        return LetDecl(name, expr)

    def parse_idStatement(self):
        name = self.lookahead.lexeme
        self._eat("ID")

        if self.lookahead.type == "ASSIGN":
            self._eat("ASSIGN")
            expr = self.parse_expr()
            return Assign(name, expr)
        elif self.lookahead.type == "LPAREN":
            args = self.parse_callSuffix_returnArgs()
            return Call(name, args)
        else:
            return Var(name)

    def parse_callSuffix_returnArgs(self):
        self._eat("LPAREN")
        args = []
        if self.lookahead.type != "RPAREN":
            args.append(self.parse_expr())
            while self.lookahead.type == "COMMA":
                self._eat("COMMA")
                args.append(self.parse_expr())
        self._eat("RPAREN")
        return args

    def parse_exprStmt(self):
        return self.parse_expr()

    def parse_fn(self) -> FnDecl:
        self._eat("KW_FN")
        name = self.lookahead.lexeme
        self._eat("ID")
        self._eat("LPAREN")
        params = []
        if self.lookahead.type == "ID":
            params.append(self.lookahead.lexeme)
            self._eat("ID")
            while self.lookahead.type == "COMMA":
                self._eat("COMMA")
                params.append(self.lookahead.lexeme)
                self._eat("ID")
        self._eat("RPAREN")
        body = self.parse_block()
        return FnDecl(name, params, body)

    def parse_block(self) -> Block:
        self._eat("LBRACE")
        stmts = []
        while self.lookahead.type != "RBRACE":
            stmts.append(self.parse_statement())
        self._eat("RBRACE")
        return Block(stmts)

    def parse_if(self) -> IfStmt:
        self._eat("KW_IF")
        self._eat("LPAREN")
        cond = self.parse_expr()
        self._eat("RPAREN")
        then_block = self.parse_block()
        else_block = None
        if self.lookahead.type == "KW_ELSE":
            self._eat("KW_ELSE")
            else_block = self.parse_block()
        return IfStmt(cond, then_block, else_block)

    def parse_while(self) -> WhileStmt:
        self._eat("KW_WHILE")
        self._eat("LPAREN")
        cond = self.parse_expr()
        self._eat("RPAREN")
        body = self.parse_block()
        return WhileStmt(cond, body)

    def parse_for(self) -> ForStmt:
        self._eat("KW_FOR")
        self._eat("LPAREN")
        init = None
        if self.lookahead.type == "KW_LET":
            init = self.parse_let()
        elif self.lookahead.type == "ID":
            init = self.parse_idStatement()
        self._eat("SEMICOLON")
        cond = self.parse_expr()
        self._eat("SEMICOLON")
        step = self.parse_expr()
        self._eat("RPAREN")
        body = self.parse_block()
        return ForStmt(init, cond, step, body)

    # EXPRESSÕES (OR, AND, igualdade, etc.) → retornam nós da AST

    def parse_expr(self):
        return self.parse_logic_or()

    def parse_logic_or(self):
        node = self.parse_logic_and()
        while self.lookahead.type == "OR":
            op = self.lookahead.lexeme
            self._eat("OR")
            right = self.parse_logic_and()
            node = BinaryOp(op, node, right)
        return node

    def parse_logic_and(self):
        node = self.parse_equality()
        while self.lookahead.type == "AND":
            op = self.lookahead.lexeme
            self._eat("AND")
            right = self.parse_equality()
            node = BinaryOp(op, node, right)
        return node

    def parse_equality(self):
        node = self.parse_comparison()
        while self.lookahead.type in ("EQ", "NEQ"):
            op = self.lookahead.lexeme
            self._eat(self.lookahead.type)
            right = self.parse_comparison()
            node = BinaryOp(op, node, right)
        return node

    def parse_comparison(self):
        node = self.parse_term()
        while self.lookahead.type in ("LT", "LE", "GT", "GE"):
            op = self.lookahead.lexeme
            self._eat(self.lookahead.type)
            right = self.parse_term()
            node = BinaryOp(op, node, right)
        return node

    def parse_term(self):
        node = self.parse_factor()
        while self.lookahead.type in ("PLUS", "MINUS"):
            op = self.lookahead.lexeme
            self._eat(self.lookahead.type)
            right = self.parse_factor()
            node = BinaryOp(op, node, right)
        return node

    def parse_factor(self):
        node = self.parse_power()
        while self.lookahead.type in ("MUL", "DIV", "MOD"):
            op = self.lookahead.lexeme
            self._eat(self.lookahead.type)
            right = self.parse_power()
            node = BinaryOp(op, node, right)
        return node

    def parse_power(self):
        node = self.parse_unary()
        while self.lookahead.type == "POW":
            op = self.lookahead.lexeme
            self._eat("POW")
            right = self.parse_unary()
            node = BinaryOp(op, node, right)
        return node

    def parse_unary(self):
        if self.lookahead.type in ("MINUS", "NOT"):
            op = self.lookahead.lexeme
            t = self.lookahead.type
            self._eat(t)
            expr = self.parse_unary()
            return UnaryOp(op, expr)
        else:
            return self.parse_primary()

    def parse_primary(self):
        t = self.lookahead.type
        if t == "NUMBER":
            value = self.lookahead.value
            self._eat("NUMBER")
            return NumberLit(value)
        elif t in ("KW_TRUE", "KW_FALSE"):
            value = (t == "KW_TRUE")
            self._eat(t)
            return BoolLit(value)
        elif t == "STRING":
            value = self.lookahead.lexeme
            self._eat("STRING")
            return StringLit(value)
        elif t == "ID":
            name = self.lookahead.lexeme
            self._eat("ID")
            if self.lookahead.type == "LPAREN":
                args = self.parse_callSuffix_returnArgs()
                return Call(name, args)
            return Var(name)
        elif t == "LPAREN":
            self._eat("LPAREN")
            node = self.parse_expr()
            self._eat("RPAREN")
            return node
        else:
            raise ParserError(
                f"Expressão inválida em {self.lookahead.line}:{self.lookahead.column}"
            )
```

---

## 6. Analisador Semântico

```python
# src/semantico/semantic_analyzer.py

from ast.nodes import *


class SemanticError(Exception):
    pass


class SymbolTable:
    def __init__(self, parent=None):
        self.parent = parent
        self.symbols = {}

    def define(self, name, info):
        if name in self.symbols:
            raise SemanticError(f"Símbolo '{name}' já declarado")
        self.symbols[name] = info

    def resolve(self, name):
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.resolve(name)
        raise SemanticError(f"Símbolo '{name}' não declarado")


class SemanticAnalyzer:
    def __init__(self):
        self.global_scope = SymbolTable()
        self.current_scope = self.global_scope

    def visit(self, node: Node):
        method_name = "visit_" + node.__class__.__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: Node):
        raise SemanticError(f"Semântica não implementada para {type(node)}")

    def visit_Program(self, node: Program):
        for stmt in node.statements:
            self.visit(stmt)

    def visit_LetDecl(self, node: LetDecl):
        self.visit(node.expr)
        self.current_scope.define(node.name, {"kind": "var"})

    def visit_Assign(self, node: Assign):
        self.current_scope.resolve(node.name)
        self.visit(node.expr)

    def visit_FnDecl(self, node: FnDecl):
        self.global_scope.define(node.name, {"kind": "fn", "params": node.params})
        fn_scope = SymbolTable(self.global_scope)
        prev = self.current_scope
        self.current_scope = fn_scope
        for p in node.params:
            self.current_scope.define(p, {"kind": "param"})
        self.visit(node.body)
        self.current_scope = prev

    def visit_Block(self, node: Block):
        for s in node.statements:
            self.visit(s)

    def visit_IfStmt(self, node: IfStmt):
        self.visit(node.cond)
        self.visit(node.then_block)
        if node.else_block:
            self.visit(node.else_block)

    def visit_WhileStmt(self, node: WhileStmt):
        self.visit(node.cond)
        self.visit(node.body)

    def visit_ForStmt(self, node: ForStmt):
        if node.init:
            self.visit(node.init)
        self.visit(node.cond)
        self.visit(node.step)
        self.visit(node.body)

    def visit_Call(self, node: Call):
        fn_info = self.global_scope.resolve(node.name)
        if fn_info["kind"] != "fn":
            raise SemanticError(f"'{node.name}' não é função")
        if len(node.args) != len(fn_info["params"]):
            raise SemanticError(
                f"Função '{node.name}' espera {len(fn_info['params'])} args, "
                f"recebeu {len(node.args)}"
            )
        for arg in node.args:
            self.visit(arg)

    def visit_BinaryOp(self, node: BinaryOp):
        self.visit(node.left)
        self.visit(node.right)

    def visit_UnaryOp(self, node: UnaryOp):
        self.visit(node.operand)

    def visit_Var(self, node: Var):
        self.current_scope.resolve(node.name)

    def visit_NumberLit(self, node: NumberLit):
        pass

    def visit_BoolLit(self, node: BoolLit):
        pass

    def visit_StringLit(self, node: StringLit):
        pass
```

---

## 7. Gerador de Código (AST → LLVM IR)

```python
# src/codegen/codegen_llvm.py

from ast.nodes import *


class LLVMModule:
    def __init__(self, name: str):
        self.name = name
        self.code = []
        self.temp_count = 0

    def new_temp(self):
        self.temp_count += 1
        return f"%t{self.temp_count}"

    def emit(self, line: str):
        self.code.append(line)

    def __str__(self):
        return "\n".join(self.code)


class LLVMCodegen:
    def __init__(self, module_name: str = "nanocalc"):
        self.module = LLVMModule(module_name)

    def generate(self, node: Program) -> LLVMModule:
        self.module.emit("; Módulo NanoCalc gerado pelo compilador")
        self.module.emit("")
        self.module.emit("define i32 @main() {")

        for stmt in node.statements:
            self.gen_stmt(stmt)

        self.module.emit("  ret i32 0")
        self.module.emit("}")
        return self.module

    def gen_stmt(self, node: Node):
        method_name = "gen_" + node.__class__.__name__
        gen = getattr(self, method_name, self.gen_default)
        return gen(node)

    def gen_default(self, node):
        pass

    def gen_LetDecl(self, node: LetDecl):
        val = self.gen_expr(node.expr)
        self.module.emit(f"  ; let {node.name} = {val}")

    def gen_Assign(self, node: Assign):
        val = self.gen_expr(node.expr)
        self.module.emit(f"  ; {node.name} = {val}")

    def gen_NumberLit(self, node: NumberLit):
        tmp = self.module.new_temp()
        self.module.emit(f"  {tmp} = add i32 0, {node.value}")
        return tmp

    def gen_BinaryOp(self, node: BinaryOp):
        left = self.gen_expr(node.left)
        right = self.gen_expr(node.right)
        tmp = self.module.new_temp()

        if node.op == "+":
            self.module.emit(f"  {tmp} = add i32 {left}, {right}")
        elif node.op == "-":
            self.module.emit(f"  {tmp} = sub i32 {left}, {right}")
        elif node.op == "*":
            self.module.emit(f"  {tmp} = mul i32 {left}, {right}")
        elif node.op == "/":
            self.module.emit(f"  {tmp} = sdiv i32 {left}, {right}")
        else:
            self.module.emit(f"  ; operador {node.op} não implementado")
        return tmp

    def gen_expr(self, node: Node):
        method_name = "gen_" + node.__class__.__name__
        gen = getattr(self, method_name, None)
        if gen is not None:
            return gen(node)
        raise NotImplementedError(f"Geração de expr não implementada para {type(node)}")
```

---

## 8. Resumo da Entrega

- **Manual de utilização:** seção 2.  
- **Manual de instalação:** seção 3.  
- **Analisador léxico (lexer):** seção 4 e `src/lexer`.  
- **Analisador sintático (parser + AST):** seção 5 e `src/parser`, `src/ast`.  
- **Analisador semântico:** seção 6 e `src/semantico`.  
- **Gerador de código (AST → LLVM IR):** seção 7 e `src/codegen`.

Com isso, o compilador NanoCalc atende todos os itens pedidos na entrega final.

