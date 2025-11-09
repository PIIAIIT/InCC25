from ply.lex import Lexer, lex

module = __import__(__name__)

tokens = list()
op_assigns = list()


def rule_lexer(doc, name, func=lambda x: x, b_assign=False):
    def f(t):
        return func(t)

    if b_assign:
        op_assigns.append(name)
    tokens.append(name)
    f.__doc__ = doc
    setattr(module, f"t_{name.upper()}", f)


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
rule_lexer(r"{", "BEGIN")
rule_lexer(r"}", "END")
rule_lexer(r"->", "ARROW")
rule_lexer(r"\.", "DOT")
rule_lexer(r",", "COMMA")

for op, name in {
    r"\+:=": "PLUS_ASSIGN",
    r"-:=": "MINUS_ASSIGN",
    r"\*\*:=": "POWER_ASSIGN",
    r"\*:=": "TIMES_ASSIGN",
    r"/:=": "DIVIDE_CEIL_ASSIGN",
    r"\\:=": "DIVIDE_FLOOR_ASSIGN",
    r"\|:=": "DIVIDE_ASSIGN",
    r"=:=": "EQUALS_ASSIGN",
    r"!=:=": "UNEQUALS_ASSIGN",
    r">=:=": "GREATER_EQUALS_ASSIGN",
    r"<=:=": "SMALLER_EQUALS_ASSIGN",
    r">:=": "GREATER_THAN_ASSIGN",
    r"<:=": "SMALLER_THAN_ASSIGN",
}.items():
    rule_lexer(op, name, b_assign=True)

for op, name in {
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
    "&": "CONS",
}.items():
    rule_lexer(op, name)

reserved = {
    "not": "NOT",
    "imag": "IMAG",
    "and:=": "AND_ASSIGN",
    "or:=": "OR_ASSIGN",
    "xor:=": "XOR_ASSIGN",
    "mod:=": "MOD_ASSIGN",
    "e:=": "EXP_ASSIGN",
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
    "sei": "LET",  # letrec
    "i64": "T_INT",
    "f64": "T_FLOAT",
    "str": "T_STRING",
    "c64": "T_COMPLEX",
    "undef": "T_UNDEF",
}
tokens += reserved.values()
op_assigns += ["AND_ASSIGN", "OR_ASSIGN", "XOR_ASSIGN", "MOD_ASSIGN", "EXP_ASSIGN"]


def assign_token_type(token):
    token.type = reserved.get(token.value, "IDENTIFIER")
    return token


rule_lexer(
    r"(?:[^\W\d_]|[\U0001F300-\U0001FAFF_])(?:[^\W_]|[\d_]|[\U0001F300-\U0001FAFF])*",
    "IDENTIFIER",
    func=assign_token_type,
)


t_ignore = " \t"
t_ignore_comment = r"\#[^\#]*\#"


def t_newline(t):
    r"\n+"
    t.lexer.lineno += len(t.value)


########### TRACEBACK #########
def print_traceback(input_text, token, silent=False):
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
    line_start = input_text.rfind("\n", 0, pos) + 1
    col = pos - line_start

    if not silent:
        print(
            f"SyntaxError: Unerwartetes Token '{token.value}' ({token.type}) in Zeile {line_num}, Spalte {col + 1}:"
        )
        print(f"    {line}")
        print(f"    {' ' * col}^")
    return (
        f"SyntaxError: Unerwartetes Token '{token.value}' ({token.type}) in Zeile {line_num}, Spalte {col + 1}:"
        + "\n"
        + f"    {line}"
        + "\n"
        + f"    {' ' * col}^"
    )


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
