# Analisador Léxico — Implementação Final (NanoCalc)

Este documento descreve a implementação final do **analisador léxico** da linguagem **NanoCalc**, incluindo:

- Conversão **AFN → AFD** (algoritmo de construção de subconjuntos);
- Implementação do **princípio do *match mais longo***;
- Definição da **estrutura de `Token`**;
- **Bufferização** da entrada;
- **Integração com o analisador sintático**;
- Diagrama **Mermaid** representando o AFD final.

> Os exemplos abaixo estão em **Python**, mas a lógica é independente da linguagem.  
> Você pode adaptar para C/Java seguindo a mesma organização de estruturas e funções.

---

## 1. Estruturas básicas: AFN, AFD e Token

### 1.1 Estrutura do AFN e AFD

```python
# src/lexer/afn_to_afd.py

from dataclasses import dataclass
from collections import deque
from typing import Dict, Set, Tuple, FrozenSet, Optional

EPSILON = ""  # símbolo de transição vazia (ε)


@dataclass
class AFN:
    """
    Autômato Finito Não-Determinístico (AFN).
    - states: conjunto de estados (ex.: {0, 1, 2, 3})
    - alphabet: conjunto de símbolos do alfabeto (chars), incluindo EPSILON
    - transitions: dict[(estado, símbolo)] -> {estados de destino}
    - start_state: estado inicial (int)
    - accepting: dict[estado] -> tipo de token (string)
    """
    states: Set[int]
    alphabet: Set[str]
    transitions: Dict[Tuple[int, str], Set[int]]
    start_state: int
    accepting: Dict[int, str]


@dataclass
class AFD:
    """
    Autômato Finito Determinístico (AFD) resultante do AFN.
    - states: conjunto de estados do AFD (ints)
    - alphabet: conjunto de símbolos (SEM epsilon)
    - transitions: dict[(estado, símbolo)] -> estado de destino
    - start_state: estado inicial
    - accepting: dict[estado] -> tipo de token (string)
    """
    states: Set[int]
    alphabet: Set[str]
    transitions: Dict[Tuple[int, str], int]
    start_state: int
    accepting: Dict[int, str]
```

### 1.2 Estrutura do Token

O **Token** carrega:

- o **tipo** (categoria léxica, ex.: `ID`, `NUMBER`, `PLUS`, `KW_LET`),
- o **lexema** (texto lido),
- a **linha** e **coluna** de início,
- opcionalmente um **valor semântico** (ex.: inteiro convertido).

```python
# src/lexer/token.py

from dataclasses import dataclass
from typing import Any


@dataclass
class Token:
    type: str      # categoria léxica (ID, NUMBER, KW_LET, PLUS, etc.)
    lexeme: str    # texto exatamente como aparece no código
    line: int      # linha de início
    column: int    # coluna de início
    value: Any = None  # valor semântico opcional (ex.: int(lexeme) para NUMBER)

    def __repr__(self) -> str:
        return f"Token(type={self.type!r}, lexeme={self.lexeme!r}, line={self.line}, column={self.column})"
```

---

## 2. Conversão AFN → AFD (algoritmo de construção de subconjuntos)

### 2.1 Fecho-ε e movimento

```python
# src/lexer/afn_to_afd.py  (continuação)

def epsilon_closure(afn: AFN, states: Set[int]) -> FrozenSet[int]:
    """
    E(S) = S ∪ { estados alcançáveis por ε a partir de S }.
    """
    stack = list(states)
    closure = set(states)

    while stack:
        s = stack.pop()
        for nxt in afn.transitions.get((s, EPSILON), set()):
            if nxt not in closure:
                closure.add(nxt)
                stack.append(nxt)

    return frozenset(closure)


def move(afn: AFN, states: FrozenSet[int], symbol: str) -> Set[int]:
    """
    move(S, a) = { t | ∃ s ∈ S tal que δ(s, a) contém t }.
    """
    result: Set[int] = set()
    for s in states:
        result |= afn.transitions.get((s, symbol), set())
    return result
```

### 2.2 Escolha de token em estados de aceitação

Quando um estado do AFD representa um conjunto de estados do AFN, vários deles podem ser finais.  
Precisamos escolher **qual token** associar a esse estado do AFD.

Aqui usamos a **prioridade implícita por menor id de estado**.  
Se você tiver prioridade explícita (ex.: `(precedence, type)`), basta adaptar.

```python
def choose_token(afn: AFN, nfa_states: FrozenSet[int]) -> Optional[str]:
    """
    Dado um conjunto de estados do AFN, escolhe o tipo de token
    associado ao estado de menor índice que seja de aceitação.
    """
    accepting_states = [s for s in nfa_states if s in afn.accepting]
    if not accepting_states:
        return None

    best_state = min(accepting_states)
    return afn.accepting[best_state]
```

### 2.3 Algoritmo de construção de subconjuntos (AFN → AFD)

```python
def afn_to_afd(afn: AFN) -> AFD:
    """
    Implementação do algoritmo de construção de subconjuntos.

    1. Estado inicial do AFD = ε-fecho({q0})
    2. Para cada estado T do AFD e cada símbolo a do alfabeto:
       - U = ε-fecho(move(T, a))
       - se U ainda não for estado do AFD, adiciona em d_states
       - cria transição T --a--> U

    Também associamos estados do AFD a tipos de token
    usando choose_token.
    """
    d_states: Dict[FrozenSet[int], int] = {}
    d_accepting: Dict[int, str] = {}
    d_transitions: Dict[Tuple[int, str], int] = {}

    # 1. estado inicial
    start_closure = epsilon_closure(afn, {afn.start_state})
    d_states[start_closure] = 0

    token_type = choose_token(afn, start_closure)
    if token_type is not None:
        d_accepting[0] = token_type

    queue = deque([start_closure])

    while queue:
        current_set = queue.popleft()
        current_id = d_states[current_set]

        for symbol in afn.alphabet:
            if symbol == EPSILON:
                continue

            next_nfa_states = move(afn, current_set, symbol)
            if not next_nfa_states:
                continue

            next_closure = epsilon_closure(afn, next_nfa_states)

            if next_closure not in d_states:
                new_id = len(d_states)
                d_states[next_closure] = new_id

                token_type = choose_token(afn, next_closure)
                if token_type is not None:
                    d_accepting[new_id] = token_type

                queue.append(next_closure)

            d_transitions[(current_id, symbol)] = d_states[next_closure]

    afd = AFD(
        states=set(d_states.values()),
        alphabet={a for a in afn.alphabet if a != EPSILON},
        transitions=d_transitions,
        start_state=0,
        accepting=d_accepting,
    )
    return afd
```

---

## 3. Bufferização da entrada

### 3.1 Ideia geral

Em implementações clássicas (como as do material do professor), usa‑se um esquema de **dois buffers** com sentinelas:

- dois blocos de tamanho fixo em um vetor,
- quando o ponteiro chega ao final do primeiro, carrega o segundo, e vice‑versa,
- evita ler caractere por caractere do disco.

Em Python, ler o arquivo inteiro em memória já é eficiente para códigos pequenos.  
Ainda assim, para **seguir a ideia de bufferização**, vamos encapsular o acesso em uma classe `InputBuffer`.

### 3.2 Classe `InputBuffer`

```python
# src/lexer/buffer.py

from typing import Optional, TextIO


class InputBuffer:
    """
    Buffer de entrada simples.

    Encapsula um arquivo ou string e fornece operações de:
    - peek(): olha o próximo caractere sem consumir;
    - advance(): consome um caractere;
    - eof(): verifica fim de arquivo.

    Em C/Java, aqui ficaria a lógica de dois buffers com sentinelas
    descrita no material do professor.
    """

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1

    @classmethod
    def from_file(cls, f: TextIO) -> "InputBuffer":
        return cls(f.read())

    def peek(self) -> Optional[str]:
        if self.pos >= len(self.text):
            return None
        return self.text[self.pos]

    def advance(self) -> Optional[str]:
        ch = self.peek()
        if ch is None:
            return None

        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def eof(self) -> bool:
        return self.peek() is None

    def get_position(self):
        return self.pos, self.line, self.col

    def set_position(self, pos: int, line: int, col: int):
        self.pos = pos
        self.line = line
        self.col = col
```

---

## 4. Lexer com *match mais longo* + bufferização

Aqui vem o **coração** do analisador léxico.

### 4.1 Princípio do *match mais longo* (maximal munch)

A ideia é:

1. Começar do estado inicial do AFD;
2. Consumir caracteres enquanto houver transição;
3. Guardar sempre o **último estado de aceitação encontrado** e a posição correspondente;
4. Quando não houver mais transição, **voltar** para a última posição de aceitação e emitir o token;
5. Se nenhum estado de aceitação foi visitado, lançar erro léxico.

Isso garante que, entre todas as formas possíveis de reconhecer um token a partir daquela posição, escolhemos o **lexema mais longo**.

### 4.2 Implementação do `Lexer`

```python
# src/lexer/lexer.py

from typing import Dict, Tuple, Optional
from .afn_to_afd import AFD
from .token import Token
from .buffer import InputBuffer


class LexicalError(Exception):
    pass


class Lexer:
    def __init__(self, buffer: InputBuffer, afd: AFD, whitespace: str = " \t\r\n") -> None:
        self.buffer = buffer
        self.afd = afd
        self.whitespace = set(whitespace)

        # Palavras reservadas da linguagem NanoCalc (exemplos)
        self.reserved_words: Dict[str, str] = {
            "let": "KW_LET",
            "fn": "KW_FN",
            "if": "KW_IF",
            "else": "KW_ELSE",
            "while": "KW_WHILE",
            "for": "KW_FOR",
            "true": "KW_TRUE",
            "false": "KW_FALSE",
        }

    # ------------- utilitários internos -------------

    def _skip_whitespace(self) -> None:
        while True:
            ch = self.buffer.peek()
            if ch is not None and ch in self.whitespace:
                self.buffer.advance()
            else:
                break

    # ------------- API pública -------------

    def next_token(self) -> Token:
        """
        Retorna o próximo token, aplicando o princípio do match mais longo.

        - Pula espaços em branco;
        - Se fim de arquivo, retorna token EOF;
        - Caso contrário, usa o AFD para consumir o maior lexema possível.
        """
        self._skip_whitespace()

        ch = self.buffer.peek()
        if ch is None:
            # EOF: usamos o estado atual da linha/coluna
            _, line, col = self.buffer.get_position()
            return Token("EOF", "", line, col)

        # Salva posição inicial do token
        start_pos, start_line, start_col = self.buffer.get_position()

        current_state = self.afd.start_state
        last_accept_state: Optional[int] = None
        last_accept_pos: Optional[Tuple[int, int, int]] = None
        last_accept_type: Optional[str] = None

        # Consome caractere a caractere enquanto houver transição
        while True:
            ch = self.buffer.peek()
            if ch is None:
                break

            key = (current_state, ch)
            if key not in self.afd.transitions:
                break

            # segue transição
            current_state = self.afd.transitions[key]
            self.buffer.advance()  # consome o caractere

            # se for estado de aceitação, atualiza o último match
            if current_state in self.afd.accepting:
                last_accept_state = current_state
                last_accept_type = self.afd.accepting[current_state]
                last_accept_pos = self.buffer.get_position()

        # Se nunca atingimos um estado de aceitação, é erro léxico
        if last_accept_state is None or last_accept_pos is None:
            # pega pequeno trecho para debug
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

        # PRINCÍPIO DO MATCH MAIS LONGO:
        # voltamos para a última posição aceita (não ficamos com lexemas parciais)
        end_pos, end_line, end_col = last_accept_pos
        self.buffer.set_position(end_pos, end_line, end_col)

        # recupera lexema a partir do texto original
        full_text = self.buffer.text
        lexeme = full_text[start_pos:end_pos]

        token_type = last_accept_type

        # Se for identificador, verifica se é palavra reservada
        if token_type == "ID" and lexeme in self.reserved_words:
            token_type = self.reserved_words[lexeme]

        # valor semântico (ex.: converte NUMBER para int)
        value = None
        if token_type == "NUMBER":
            try:
                value = int(lexeme)
            except ValueError:
                # se a sintaxe do número for mais complexa (float, etc.), trate aqui
                value = None

        return Token(token_type, lexeme, start_line, start_col, value)

    def tokenize(self):
        """Retorna a lista completa de tokens, incluindo EOF."""
        tokens = []
        while True:
            tok = self.next_token()
            tokens.append(tok)
            if tok.type == "EOF":
                break
        return tokens
```

---

## 5. Integração com a Análise Sintática

Para integrar o **lexer** com o **parser** (analisador sintático), seguimos o padrão:

- O parser mantém um **token de lookahead**;
- Quando consome um símbolo da gramática, chama `next_token()`;
- O parser não se preocupa com lexemas ou caracteres individuais, apenas com tipos de token (`ID`, `NUMBER`, `KW_LET`, etc.).

### 5.1 Exemplo de uso do Lexer

```python
# src/main.py (exemplo de uso)

from pathlib import Path
from lexer.afn_to_afd import AFN, afn_to_afd, EPSILON
from lexer.buffer import InputBuffer
from lexer.lexer import Lexer
from lexer.token import Token


def construir_afn_nano_calc() -> AFN:
    """
    Constrói o AFN da linguagem NanoCalc com base na especificação léxica.
    Aqui você deve usar o AFN que já foi desenvolvido nas etapas anteriores.
    """
    # TODO: implementar de acordo com a especificação de tokens
    raise NotImplementedError("Construa o AFN da NanoCalc aqui")


def main():
    source_path = Path("exemplos/programa.nano")
    text = source_path.read_text(encoding="utf-8")

    afn = construir_afn_nano_calc()
    afd = afn_to_afd(afn)

    buffer = InputBuffer(text)
    lexer = Lexer(buffer, afd)

    for token in lexer.tokenize():
        print(token)


if __name__ == "__main__":
    main()
```

### 5.2 Esqueleto de Parser com integração ao Lexer

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

    def _eat(self, expected_type: str):
        if self.lookahead.type == expected_type:
            self.lookahead = self.lexer.next_token()
        else:
            raise ParserError(
                f"Esperado {expected_type}, encontrado {self.lookahead.type} "
                f"na linha {self.lookahead.line}, coluna {self.lookahead.column}"
            )

    # Exemplo: <program> ::= { <statement> }
    def parse_program(self):
        while self.lookahead.type != "EOF":
            self.parse_statement()

    # Aqui viriam os métodos parse_statement, parse_expr, etc.
```

---

## 6. Diagrama Mermaid do AFD Final

> **IMPORTANTE:** Este diagrama é um **modelo**.  
> Você deve ajustá-lo para refletir o AFD específico gerado a partir do seu AFN
> (estados, transições e estados de aceitação).

Salve o conteúdo abaixo em `docs/diagramas/afd_final.md`:

```mermaid
graph LR
    %% Estado inicial
    qi(( )) --> q0((q0))

    %% Exemplo de caminhos para alguns tokens

    %% Identificadores / palavras reservadas: ID / KW_*
    q0 -->|letra| q1((q1))
    q1 -->|letra, digito, _| q1

    %% Números inteiros: NUMBER
    q0 -->|digito| q2((q2))
    q2 -->|digito| q2

    %% Operadores simples
    q0 -->|"+"| q3((q3))
    q0 -->|"-"| q4((q4))
    q0 -->|"*"| q5((q5))
    q0 -->|"/"| q6((q6))

    %% Operadores relacionais (exemplo de >=, <=, ==, !=)
    q0 -->|"<"| q7((q7))
    q0 -->|">"| q8((q8))
    q0 -->|"="| q9((q9))
    q0 -->|"!"| q10((q10))

    q7 -->|"="| q11((q11))   %% <=
    q8 -->|"="| q12((q12))   %% >=
    q9 -->|"="| q13((q13))   %% ==
    q10 -->|"="| q14((q14))  %% !=

    classDef final fill:#cfc,stroke:#333,stroke-width:2px;

    %% Estados de aceitação (exemplo)
    class q1,q2,q3,q4,q5,q6,q7,q8,q9,q10,q11,q12,q13,q14 final;
```

> Na prática, o AFD resultante pode ter bem mais estados.  
> A ideia do diagrama é ilustrar o formato e mostrar que você sabe representar
> o autômato em Mermaid.

---

## 7. Resumo dos Pontos Pedidos

- **Princípio do *match mais longo***:  
  Implementado no `Lexer.next_token()` via `last_accept_state`, `last_accept_pos` e `set_position()` para voltar à última posição aceita.

- **Estrutura do token**:  
  Definida em `token.py` com `type`, `lexeme`, `line`, `column` e `value`.

- **Bufferização**:  
  Encapsulada em `InputBuffer`, que pode ser refinada para o esquema de **dois buffers com sentinelas** descrito no material do professor.  
  O lexer nunca acessa o arquivo diretamente, apenas via esse buffer.

- **Integração com análise sintática**:  
  Mostrada com o esqueleto de `Parser`, que consome tokens de `Lexer` com lookahead.

Pronto: com esses arquivos (`afn_to_afd.py`, `buffer.py`, `token.py`, `lexer.py` e `afd_final.md`) ajustados à sua especificação de tokens, você tem um **analisador léxico completo**, alinhado com a teoria vista em aula e pronto para tirar 10. 😎
