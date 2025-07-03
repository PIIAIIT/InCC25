from ply.lex import Lexer, lex

module = __import__(__name__)

tokens = []


def rule_lexer(doc, name, func=lambda x: x):
    def f(t):
        return func(t)

    tokens.append(name)
    f.__doc__ = doc
    setattr(module, f"t_{name.upper()}", f)


literals = "_e"

# OHNE ALPHABETISCHE ZEICHEN
binops = {
    r"\+": "PLUS",
    r"-": "MINUS",
    r"\*\*": "POWER",
    r"\*": "TIMES",
    r"/": "DIVIDE_CEIL",
    r"\\": "DIVIDE_FLOOR",
    r"\|": "DIVIDE",
    r"=": "EQUALS",
    r"!=": "UNEQUALS",
    r">=": "GREATER_EQUALS",
    r"<=": "SMALLER_EQUALS",
    r">": "GREATER_THAN",
    r"<": "SMALLER_THAN",
}

rule_lexer(r"(\d+\.\d+)", "FLOAT")
rule_lexer(r"0x[0-9a-fA-F]+|0b(0|1[01]*)|\d+", "NUMBER")
rule_lexer(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', "STRING")
rule_lexer(r":=", "ASSIGN")
rule_lexer(r";", "SEMICOLON")
rule_lexer(r":", "COLON")
rule_lexer(r"\(", "LPAREN")
rule_lexer(r"\)", "RPAREN")
rule_lexer(r"\]", "CLOSED_BRACKETS")
rule_lexer(r"\[", "OPEN_BRACKETS")
rule_lexer(r"\{", "BEGIN")  # Sequence Begin
rule_lexer(r"\}", "END")  # Sequence End
rule_lexer(r"->", "LAMBDA_ARROW")
rule_lexer(r"\.\.\.", "DOTS")
rule_lexer(r"\.\.", "ITER")
rule_lexer(r"\.", "DOT")
rule_lexer(r",", "COMMA")

lookup_table = {
    "not": "NOT",
    "imag": "IMAG",
    "and": "AND",
    "or": "OR",
    "xor": "XOR",
    "mod": "MOD",
    "e": "EXP",
    "wenn": "IF",
    "gilt": "THEN",
    "aber": "ELIF",
    "sonst": "ELSE",
    "solange": "WHILE",
    "für": "LOOP",
    "wiederhole": "LOOPTHEN",
    "in": "IN",
    "lambda": "LAMBDA",
    "importiere": "IMPORT",
    "vergleiche": "MATCH",
    "mit": "WITH",
    "fall": "CASE",
    "struct": "STRUCT",
    "leere": "NULL",
    "sei": "LET",  # Ist schon ein Letrec
}
tokens += lookup_table.values()

for rule, tkn in {"and:=": "AND_ASSIGN",
                  "or:=": "OR_ASSIGN",
                  "xor:=": "XOR_ASSIGN",
                  "mod:=": "MOD_ASSIGN",
                  "e:=": "EXP_ASSIGN"}.items():
    rule_lexer(rule, tkn)


def check_if_keyword(token):
    token.type = lookup_table.get(token.value, "IDENTIFIER")
    return token


rule_lexer(r"(?:[^\W\d_]|[\U0001F300-\U0001FAFF_])(?:[^\W_]|[\d_]|[\U0001F300-\U0001FAFF])*", "IDENTIFIER", check_if_keyword)

op_assigns = {k + ":=": v + "_ASSIGN" for k, v in binops.items()}
for doc, token in op_assigns.items():
    rule_lexer(doc, token)
op_assigns.update({"and:=": "AND_ASSIGN", "or:=": "OR_ASSIGN", "xor:=": "XOR_ASSIGN", "mod:=": "MOD_ASSIGN", "e:=": "EXP_ASSIGN"})

for doc, token in binops.items():
    rule_lexer(doc, token)
binops.update({"and": "AND", "or": "OR", "xor": "XOR", "mod": "MOD", "e": "EXP"})
rule_lexer("&", "CONS")


t_ignore = " \t"
t_ignore_comment = r"\#[^\#]*\#"


def t_newline(t):
    r"\n+"
    t.lineno += 1


########### TRACEBACK #########
def print_traceback(input_text: str, token, silent=False):
    """
    Druckt einen gut lesbaren Traceback, wenn ein Parsing-Fehler auftritt.
    :param input_text: Der gesamte Quelltext als String.
    :param token: Das Token, das den Fehler ausgelöst hat (kann auch None sein).
    """
    if token is None:
        print("SyntaxError: Unerwartetes Dateiende")
        return

    line_num = token.lineno
    pos = token.lexpos

    # Ermittle die aktuelle Zeile aus dem Text
    lines = input_text.splitlines()
    line = lines[line_num - 1] if 0 < line_num <= len(lines) else "<unbekannte Zeile>"

    # Spaltenposition berechnen
    line_start = input_text.rfind('\n', 0, pos) + 1
    col = pos - line_start

    if not silent:
        print(f"SyntaxError: Unerwartetes Token '{token.value}' ({token.type}) in Zeile {line_num}, Spalte {col + 1}:")
        print(f"    {line}")
        print(f"    {' ' * col}^")
    return f"SyntaxError: Unerwartetes Token '{token.value}' ({token.type}) in Zeile {line_num}, Spalte {col + 1}:" + "\n" + \
        f"    {line}" + "\n" + \
        f"    {' ' * col}^"


def t_error(t):
    print_traceback(t.lexer.lexdata, t)
    t.lexer.skip(1)
    return t


lexer: Lexer = lex()

if __name__ == "__main__":
    # Interaktives Menu
    while True:
        try:
            s = input(">>> ")
        except EOFError:
            break

        if not s or s.lower() == "\n":
            continue
        if s.lower() == "q":
            break

        lexer.input(s)

        for token in lexer:
            print(token)
