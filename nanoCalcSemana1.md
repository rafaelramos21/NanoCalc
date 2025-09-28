# NanoCalc — Semana 1: Especificação Léxica e Exemplos (Foco em Cálculos Rápidos)

## 📋 Objetivos da Semana
Aplicar conceitos de **alfabetos, palavras e linguagens** para definir o **alfabeto** e os **tokens** do **NanoCalc**, uma linguagem minimalista para **contas científicas rápidas** (sem tipos explícitos, sem boilerplate, com REPL e scripts `.nano`).

---

## 🎯 Diretrizes de Usabilidade (NanoCalc)
- **Sem ponto-e-vírgula** e sem declarações de tipo; a linguagem é **orientada a expressões**.
- **Atribuição** com `let` e reatribuição direta: `let x = 2`, depois `x = x + 3`.
- **Listas/Vetores** com `[...]` e **matrizes** com `[[...], [...]]`.
- **Funções** definidas com `fn nome(args) { ... }` e `return` opcional (última expressão vale).
- **Comentários** com `# ...` (linha) ou `/* ... */` (bloco, sem aninhamento).
- **Whitespace** livre (ignorado fora de strings). **Case‑sensitive**.
- **Foco em matemática**: built-ins para trigonometria, estatística, álgebra linear básica.

---

## 📊 Entrega da Semana
- ✅ Especificação completa do **alfabeto (Σ)**.  
- ✅ Definição formal de **tokens** por ER.  
- ✅ Exemplos **válidos** de programas NanoCalc.  

---

## 1) Alfabeto (Σ)
Conjunto de caracteres aceitos no código-fonte (UTF-8):

- Letras: `A–Z`, `a–z` (acentos permitidos mas **desencorajados** por portabilidade)
- Dígitos: `0–9`
- Sublinhado: `_`
- Operadores: `+ - * / ^ % = == != < <= > >= && || !`
- Delimitadores: `(` `)` `[` `]` `{` `}` `,` `:`
- Ponto decimal: `.`
- Aspas: `'` e `"`
- Comentários: `#`, `/*`, `*/`
- Espaço em branco: espaço, tab, `\n`, `\r\n`

> Implementações devem ser *Unicode-aware*; arquivos em **UTF-8**.

---

## 2) Tokens (Definição Formal por ER)

### 2.1 Ignoráveis
- **WHITESPACE**: `[\\t\\f\\r\\n ]+`  
- **COMMENT_LINE**: `#[^\\n]*`  
- **COMMENT_BLOCK**: `/\\*[^*]*\\*+(?:[^/*][^*]*\\*+)*/`  

### 2.2 Identificadores
- **ID**: `[A-Za-z_][A-Za-z0-9_]*`  
  > Alternativa com acentos (não recomendada para portabilidade): incluir classe de letras acentuadas no conjunto.

### 2.3 Números
- **INT**: `[0-9]+`  
- **DEC**: `(?:[0-9]+\\.[0-9]*|\\.[0-9]+)`  
- **SCI**: `(?: (?:[0-9]+(?:\\.[0-9]*)?|\\.[0-9]+) [eE] [+-]? [0-9]+ )`  
- **NUMBER**: `SCI | DEC | INT`  
  > Exemplos: `0`, `42`, `3.`, `.5`, `1e-3`, `6.02e23`

### 2.4 Strings
- **STRING**: `'([^\\\\'\\n]|\\\\.)*' | \"([^\\\\\"\\n]|\\\\.)*\"`  
  > Sem quebras de linha literais; usar `\\n`. Escapes suportados: `\\n`, `\\r`, `\\t`, `\\\"`, `\\'`, `\\\\`.

### 2.5 Operadores e Delimitadores
- **Ops 2+**: `==`, `!=`, `<=`, `>=`, `&&`, `||`  
- **Ops 1**: `+`, `-`, `*`, `/`, `^`, `%`, `=`, `<`, `>`, `!`  
- **Delims**: `(` `)` `[` `]` `{` `}` `,` `:`

### 2.6 Palavras‑chave
- **Keywords**: `let`, `fn`, `return`, `if`, `else`, `for`, `while`, `in`, `true`, `false`

### 2.7 Nomes Reservados do Ambiente (pré-definidos)
- **Constantes**: `pi`, `e`
- **Funções built-in (amostra inicial)**:  
  `sin, cos, tan, asin, acos, atan, exp, ln, log10, sqrt, abs, sum, mean, median, std, range, dot, norm, transpose, det (2x2), inv (2x2)`

---

## 3) Regras Léxicas e Ambiguidades
- **Maximal munch**: prefira o token mais longo válido (`>=` não vira `>` + `=`).  
- `-` unário vs. binário resolvido na **sintaxe**; no léxico é apenas `-`.  
- **Ponto `.`** só existe dentro de números (não há operador de acesso por ponto na versão inicial).  
- `pi` e `e` são `ID` no léxico; o **ambiente** injeta seus valores.

---

## 4) Esboço Sintático (para dar contexto aos tokens)
> O foco desta semana é **léxico**; abaixo só um recorte útil para os exemplos.

```
program     := { statement }
statement   := letDecl | assign | expr | fnDecl | ifStmt
letDecl     := "let" ID "=" expr
assign      := ID "=" expr
fnDecl      := "fn" ID "(" [paramList] ")" block
paramList   := ID { "," ID }
block       := "{" { statement } "}"
ifStmt      := "if" expr block [ "else" block ]

expr        := logic_or
logic_or    := logic_and { "||" logic_and }
logic_and   := equality  { "&&" equality  }
equality    := comparison { ("==" | "!=") comparison }
comparison  := term { ("<" | "<=" | ">" | ">=") term }
term        := factor { ("+" | "-") factor }
factor      := power  { ("*" | "/" | "%") power }
power       := unary  { "^" unary }
unary       := ["-" | "!"] primary
primary     := NUMBER | STRING | "true" | "false" | list | matrix
             | ID call? | "(" expr ")"
call        := "(" [argList] ")"
argList     := expr { "," expr }
list        := "[" [argList] "]"
matrix      := "[" [list {"," list}] "]"
```

---

## 5) Exemplos **NanoCalc** (focados em contas)

### 5.1 Álgebra rápida e trigonometria
```nano
# (a + b)^2 e identidade trigonométrica
let a = 2
let b = 3.5
(a + b)^2

let ang = pi / 6
sin(ang)^2 + cos(ang)^2  # -> 1
```

### 5.2 Estatística descritiva em uma linha
```nano
let xs = [1, 2, 2, 3, 4, 7]
mean(xs)        # média
median(xs)      # mediana
std(xs)         # desvio padrão populacional
sum(xs)         # soma
```

### 5.3 Álgebra linear compacta
```nano
let v = [3, 4]
norm(v)         # -> 5

let a = [1, 2, 3]
let b = [4, 5, 6]
dot(a, b)       # -> 32

let M = [[1, 2], [3, 4]]
transpose(M)    # -> [[1,3],[2,4]]
det(M)          # -> -2
inv(M)          # -> [[-2,1],[1.5,-0.5]]
```

### 5.4 Fórmula de Bhaskara (raízes de quadrática)
```nano
fn bhaskara(a, b, c) {
  let d = b^2 - 4*a*c
  if d < 0 { return [] }
  if d == 0 { return [ -b / (2*a) ] }
  let s = sqrt(d)
  [ (-b + s) / (2*a), (-b - s) / (2*a) ]
}

bhaskara(1, -3, 2)  # -> [2, 1]
```

### 5.5 Integração numérica simples (Regra do Trapézio)
```nano
fn trapz(f, a, b, n) {
  let h = (b - a) / n
  let acc = 0
  let i = 1
  let x = a + h
  while i < n {
    acc = acc + f(x)
    x = x + h
    i = i + 1
  }
  (h/2) * (f(a) + 2*acc + f(b))
}

fn f(x) { x^2 }     # integral de x^2 de 0 a 1 -> 1/3 ≈ 0.3333
trapz(f, 0, 1, 1000)
```

### 5.6 Conversões e contas do dia a dia
```nano
# Conversão Celsius -> Fahrenheit e IMC
fn F(c) { (9/5)*c + 32 }
fn imc(peso, altura) { peso / (altura^2) }

F(25)         # -> 77
imc(70, 1.75) # -> ~22.86
```

---

📅 **Semana 1 — 22/08/2025** · Equipe: **Rafael Ribeiro Ramos** e **João Pedro**
