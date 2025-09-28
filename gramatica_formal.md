# Gramática Formal — NanoCalc

**Data:** 02/09/2025
**Autores:** Rafael Ribeiro Ramos, João Pedro (Equipe-Kamikaze)

---

## 1. Objetivo
Documento com a primeira versão formal da *gramática* da linguagem **NanoCalc**. Inclui regras de produção (EBNF/BNF), classificação na hierarquia de Chomsky, exemplos de derivações, análise de ambiguidades e estratégias de resolução.

---

## 2. Justificativa da classe gramatical
A gramática proposta é **livre de contexto (Type-2)** por conter estruturas aninhadas como expressões com parênteses, listas/matrizes, blocos `{ ... }` e chamadas de função com argumentos possivelmente recursivos. Essas estruturas exigem emparelhamento e recursão que não podem ser reconhecidas por gramáticas regulares (Type-3). Portanto classificamos como **Context-Free Grammar (CFG)**.

**Por que não regular?**
- Expressões arbitrariamente aninhadas `(...)` e blocos `{ ... }` exigem contagem/empilhamento.
- Declarações e chamadas com listas de argumentos de comprimento arbitrário.

**Potencial de otimização:** a gramática é adequada para analisadores LR(1) ou LALR(1). Para análise top‑down (LL(1)) são necessárias transformações (remoção de recursão à esquerda, factorização).

---

## 3. Notação
Usamos EBNF com convenções:
- `<NonTerminal>` — não terminal
- Terminais são literais como `let`, `fn`, `(`, `)`, `+` etc.
- `|` — alternativa
- `{ ... }` — 0 ou mais repetições
- `[ ... ]` — opcional
- `,` separado por vírgula conforme mostrado

---

## 4. Gramática (EBNF — versão legível)

```
<program>          ::= { <statement> }

<statement>        ::= <letDecl>
                     |  <assign>
                     |  <fnDecl>
                     |  <ifStmt>
                     |  <whileStmt>
                     |  <forStmt>
                     |  <exprStmt>

<letDecl>          ::= "let" <ID> "=" <expr>
<assign>           ::= <ID> "=" <expr>
<fnDecl>           ::= "fn" <ID> "(" [ <paramList> ] ")" <block>
<paramList>        ::= <ID> { "," <ID> }
<block>            ::= "{" { <statement> } "}"

<ifStmt>           ::= "if" "(" <expr> ")" <block> [ "else" <block> ]
<whileStmt>        ::= "while" "(" <expr> ")" <block>
<forStmt>          ::= "for" "(" <forInit> ";" <expr> ";" <expr> ")" <block>
<forInit>          ::= "let" <ID> "=" <expr> | <assign> | /* empty */

<exprStmt>         ::= <expr>

/* --- Expressões com precedência e associatividade --- */
<expr>             ::= <logic_or>
<logic_or>         ::= <logic_and> { "||" <logic_and> }
<logic_and>        ::= <equality> { "&&" <equality> }
<equality>         ::= <comparison> { ("==" | "!=") <comparison> }
<comparison>       ::= <term> { ("<" | "<=" | ">" | ">=") <term> }
<term>             ::= <factor> { ("+" | "-") <factor> }
<factor>           ::= <power> { ("*" | "/" | "%") <power> }
<power>            ::= <unary> { "^" <unary> }        /* '^' é associativo à direita */
<unary>            ::= ("-" | "!") <unary> | <primary>

<primary>          ::= <NUMBER>
                     |  <STRING>
                     |  "true" | "false"
                     |  <list>
                     |  <matrix>
                     |  <ID> [ <callSuffix> ]
                     |  "(" <expr> ")"

<callSuffix>       ::= "(" [ <argList> ] ")"
<argList>          ::= <expr> { "," <expr> }

<list>             ::= "[" [ <argList> ] "]"
<matrix>           ::= "[" <list> { "," <list> } "]"

/* Terminais: <ID>, <NUMBER>, <STRING> definidos no léxico (docs de tokens) */
```

---

## 5. Precedência e associatividade (explicitação)
- **Precedência (mais forte → mais fraco):**
  1. `^` (potenciação) — **associatividade à direita**
  2. unary `-`, `!` — **direita**
  3. `*`, `/`, `%` — **esquerda**
  4. `+`, `-` — **esquerda**
  5. `<`, `<=`, `>`, `>=` — **não-associativa** (encadear gera erro ou exigir parênteses)
  6. `==`, `!=` — **não-associativa**
  7. `&&` — **esquerda**
  8. `||` — **esquerda**

- O layout acima (várias camadas: `term`, `factor`, `power`, `unary`) implementa a precedência esperada.

---

## 6. Exemplo de derivações (passo a passo)

### 6.1 Derivação para `a + b * c` (mostrando que `*` tem precedência sobre `+`)
1. `<expr>` ⇒ `<logic_or>` ⇒ `<logic_and>` ⇒ `<equality>` ⇒ `<comparison>` ⇒ `<term>`
2. `<term>` ⇒ `<factor>` `<term'>` (equivalente a `<factor> { ("+"|"-") <factor> }`)
3. `<factor>` ⇒ `<power>` ⇒ `<unary>` ⇒ `<primary>` ⇒ `<ID>` (a)
4. agora a repetição do termo aplica `+` e um `<factor>`:
   - `<term>` ⇒ `<factor>` (`a`) `+` `<factor>`
5. segundo `<factor>` ⇒ `<power>` ⇒ `<unary>` ⇒ `<primary>` ⇒ `<ID>` (b) mas esse `<factor>` tem multiplicação `* <power>`:
   - `<factor>` ⇒ `<power>` `*` `<power>` ⇒ `<unary>` (b) `*` `<unary>` (c)
Resultado: arvore cuja subárvore `b * c` é aninhada dentro do operando do `+`, garantindo precedência.

### 6.2 Derivação para `-2^3` (unário vs potência — interpretado como `-(2^3)`)
- `<unary>` ⇒ `-` `<unary>` ⇒ `-` `<primary>` (`2^3` é construído por `<power>`: `<primary>` `^` `<unary>`)
- Com a regra de `<power> ::= <unary> { '^' <unary> }` e definindo '^' como direita-associativo, `-2^3` é `-(2^3)`.

### 6.3 Derivação de `if` com `else` (resolvendo dangling else — ver seção 8)
Ver seção 8 para uma versão com `matched`/`unmatched` para garantir que `else` caseie com o `if` mais próximo.

---

## 7. Ambiguidades potenciais e resolução

### 7.1 Ambiguidade de expressão
A gramática de expressão como escrita **não** é ambígua quanto à precedência, porque cada nível de produção implementa uma camada de precedência diferente. Isso garante que `a + b * c` gere uma única árvore de parse onde `*` fica mais profundo.

### 7.2 Dangling else (else pendente)
Padrão problema: `if e1 if e2 stmt1 else stmt2` — o `else` pode ligar ao `if` interior ou exterior.

**Solução** (clássica): separar statements em `matched` (if com else) e `unmatched` (if sem else).

```
<statement>      ::= <matched> | <unmatched> | other_statements

<matched>        ::= "if" "(" <expr> ")" <matched> "else" <matched>
                 |   <other_statement>   /* other statements that are not if */

<unmatched>      ::= "if" "(" <expr> ")" <statement>
```

Com essa separação o `else` sempre casa com o `if` mais próximo, removendo a ambiguidade.

### 7.3 Ambiguidades causadas por recursão à esquerda (para LL)
A gramática apresentada usa repetição `{ ... }` que corresponde a produção direita-recursiva/interativa, evitando ambiguidade, porém implementações diretas com recursão à esquerda exigirão transformação para LL parsers.

---

## 8. Transformações e recomendação de parser
- **Recomendação prática:** implementar um **parser LR(1) / LALR(1)** (e.g., geradores Bison, Menhir ou ANTLR com modo LR) ou usar um **Pratt parser** para expressões (mais simples e poderoso para precedência). Para um REPL/linguagem de cálculos rápidos, um Pratt parser combinado com um lexico simples é muito produtivo.

- **Caso queiram LL(1):** eliminar recursão à esquerda e fatorar alternativas. Por exemplo, para `<term>`:

```
<term> ::= <factor> <term_tail>
<term_tail> ::= ("+" | "-") <factor> <term_tail> | /* epsilon */
```

Isso transforma para forma adequada a LL(1).

---

## 9. Exemplos completos de derivação (BHASKARA)
Programa pequeno (trecho):

```
fn bhaskara(a, b, c) {
  let d = b^2 - 4*a*c
  if d < 0 { return [] }
  if d == 0 { return [ -b / (2*a) ] }
  let s = sqrt(d)
  [ (-b + s) / (2*a), (-b - s) / (2*a) ]
}
```

A derivação do `fnDecl` começa por `<fnDecl> ::= "fn" <ID> "(" [<paramList>] ")" <block>` e recursivamente deriva `<block>` com várias `<statement>` internas (letDecl, ifStmt, exprStmt). Cada expressão interna segue as regras de precedência já definidas.

---

## 10. Checklist / próximos passos
- [ ] Gerar versão EBNF compatível com ANTLR (pequenas mudanças sintáticas).
- [ ] Implementar lexer baseado nas ERs que você já definiu (WHITESPACE, ID, NUMBER, STRING, ops, delims).
- [ ] Escolher parser: **Pratt** para REPL rápido + implementações iterativas; **LR(1)** para versão robusta do compilador.
- [ ] Escrever casos‑teste que verifiquem precedência, associatividade e `dangling else`.

---

## 11. Referências conceituais
- Hopcroft & Ullman — *Introduction to Automata Theory, Languages, and Computation* (cap. gramáticas e hierarquia de Chomsky)
- Pratt parsing papers / articles (técnica para expressões com precedência)

---

