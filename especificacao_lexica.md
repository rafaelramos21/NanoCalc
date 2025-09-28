# Especificação Léxica — NanoCalc (Versão Refinada)

**Data:** 28/09/2025  
**Autores:** Rafael Ribeiro Ramos, João Pedro (Equipe-Kamikaze)

---

## 1. Objetivo
Refinar a especificação léxica da linguagem **NanoCalc**, garantindo expressões regulares não ambíguas, definição clara de precedência entre tokens e estratégias iniciais de tratamento de erros léxicos.

---

## 2. Tokens definidos por expressões regulares

### 2.1 Ignoráveis
- **WHITESPACE**: `[\t\f\r\n ]+`
- **COMMENT_LINE**: `#[^\n]*`
- **COMMENT_BLOCK**: `/\*[^*]*\*+(?:[^/*][^*]*\*+)*/`

> Esses tokens são descartados pelo analisador léxico.

---

### 2.2 Identificadores e palavras-chave
- **ID**: `[A-Za-z_][A-Za-z0-9_]*`
- **KEYWORD**: palavras reservadas listadas explicitamente.
  - Lista: `let`, `fn`, `return`, `if`, `else`, `for`, `while`, `in`, `true`, `false`

**Regra de precedência:**
1. Primeiro verificar se a sequência casa com uma palavra-chave.
2. Caso contrário, classificar como `ID`.

---

### 2.3 Números
- **INT**: `[0-9]+`
- **DEC**: `(?:[0-9]+\.[0-9]*|\.[0-9]+)`
- **SCI**: `(?: (?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+) [eE] [+-]? [0-9]+ )`
- **NUMBER**: `SCI | DEC | INT`

> Exemplos válidos: `0`, `42`, `3.`, `.5`, `1e-3`, `6.02e23`

---

### 2.4 Strings
- **STRING**: `'(?:[^\\'\n]|\\.)*' | "(?:[^\\"\n]|\\.)*"`

> Não permite quebra de linha literal. Escapes aceitos: `\n`, `\r`, `\t`, `\"`, `\'`, `\\`.

---

### 2.5 Operadores
- **OPERATORS_2**: `==|!=|<=|>=|&&|\|\|`
- **OPERATORS_1**: `[+\-*/^%=<>!]`

**Regra de precedência:**
- Aplicar **maximal munch**: tokens de 2+ caracteres são sempre reconhecidos antes de tokens unitários.

---

### 2.6 Delimitadores
- **DELIM**: `[()\[\]{},:]`

---

### 2.7 Constantes e funções built-in (pré-definidas)
- Tratadas como **ID** no léxico.
- Ambiente semântico injeta significado especial.

Ex.: `pi`, `e`, `sin`, `cos`, `sqrt` etc.

---

## 3. Estratégia de resolução de ambiguidades

### 3.1 ID vs. KEYWORD
- O analisador tenta casar palavras-chave primeiro.
- Se não encontrar, classifica como `ID`.

### 3.2 Operadores unitários vs. compostos
- Maximal munch: `>=` reconhecido como único token, nunca `>` seguido de `=`.

### 3.3 Números decimais vs. ponto isolado
- O ponto (`.`) só é aceito como parte de `DEC` ou `SCI`. Não existe operador de acesso por ponto nesta versão.

---

## 4. Tratamento de erros léxicos

### 4.1 Caracteres inválidos
- Qualquer caractere que não se encaixe em nenhuma expressão regular gera um erro léxico.
- Estratégia: reportar o caractere e a posição (linha, coluna).

Exemplo:
```
Erro léxico na linha 3, coluna 15: caractere inválido '@'
```

### 4.2 Strings malformadas
- Strings não fechadas devem gerar erro:
```
Erro léxico na linha 5: string não terminada
```

### 4.3 Comentários não fechados
- Comentários de bloco `/* ... */` não fechados também devem ser reportados:
```
Erro léxico na linha 12: comentário de bloco não terminado
```

---

## 5. Primeiros esboços de mensagens de erro
- **Caractere inválido:** "Caractere inesperado `<c>` encontrado."
- **String não terminada:** "String iniciada na linha X não foi terminada."
- **Comentário não terminado:** "Comentário de bloco iniciado na linha X não foi fechado."
- **Número malformado:** "Número inválido: `<lexema>` (verifique uso de ponto ou expoente)."

---

## 6. Reflexões
- **Eficiência:** expressões regulares foram mantidas relativamente simples, privilegiando clareza e desempenho.
- **Internacionalização:** por ora, `ID` não aceita letras acentuadas para evitar problemas de portabilidade. Mas pode ser estendido com classes Unicode (`\p{L}`) se quisermos suportar identificadores não-ASCII.
- **Equilíbrio:** priorizamos robustez na detecção de erros e clareza na definição dos tokens, mesmo que algumas expressões poderiam ser mais compactas.

---

*Fim da versão refinada da especificação léxica.*

