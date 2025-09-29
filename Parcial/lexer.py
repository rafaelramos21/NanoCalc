import sys
import re

# Definição dos tokens da NanoCalc
TOKEN_SPEC = [
    ("NUMBER",   r"\d+(\.\d+)?"),       # Números inteiros ou decimais
    ("PRINT",    r"\bprint\b"),         # Função print
    ("IDENTIFIER", r"[a-zA-Z_][a-zA-Z0-9_]*"),  # Identificadores
    ("ASSIGN",   r"="),                 # Operador de atribuição
    ("PLUS",     r"\+"),                # +
    ("MINUS",    r"-"),                 # -
    ("MULTIPLY", r"\*"),                # *
    ("DIVIDE",   r"/"),                 # /
    ("LPAREN",   r"\("),                # (
    ("RPAREN",   r"\)"),                # )
    ("NEWLINE",  r"\n"),                # Quebra de linha
    ("SKIP",     r"[ \t]+"),            # Espaços e tabs
    ("COMMENT",  r"#.*"),               # Comentários
]

# Compilar regex
token_regex = "|".join(f"(?P<{name}>{regex})" for name, regex in TOKEN_SPEC)
pattern = re.compile(token_regex)

def lexer(code):
    line_num = 1
    line_start = 0
    tokens = []

    for mo in pattern.finditer(code):
        kind = mo.lastgroup
        value = mo.group()
        column = mo.start() - line_start + 1

        if kind == "NEWLINE":
            line_num += 1
            line_start = mo.end()
        elif kind == "SKIP" or kind == "COMMENT":
            continue
        else:
            tokens.append((value, kind))
    
    # Verificar se há algum caracter inválido
    pos = 0
    while pos < len(code):
        match = pattern.match(code, pos)
        if not match:
            line = code.count("\n", 0, pos) + 1
            col = pos - code.rfind("\n", 0, pos)
            raise SyntaxError(f"Erro: token inválido '{code[pos]}' na linha {line}, coluna {col}")
        pos = match.end()
    
    return tokens

def main():
    if len(sys.argv) != 2:
        print("Uso: python lexer.py <arquivo.nanocalc>")
        sys.exit(1)
    
    filename = sys.argv[1]
    with open(filename, "r") as f:
        code = f.read()

    try:
        tokens = lexer(code)
        print(f"{'TOKEN':<15} | {'TIPO'}")
        print("-" * 25)
        for val, typ in tokens:
            print(f"{val:<15} | {typ}")
    except SyntaxError as e:
        print(e)

if __name__ == "__main__":
    main()
