from ply.lex import Lexer, lex

module = __import__(__name__)


def rule_lexer(doc, name, func=lambda x: x):
    def f(t):
        return func(t)

    f.__doc__ = doc
    setattr(module, f"t_{name.upper()}", f)


literals = "_e"

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
    "and": "AND",
    "or": "OR",
    "xor": "XOR",
    "mod": "MOD",
    "e": "EXP",
}
unary = {
    "not": "NOT",
    "imag": "IMAG",
}  # unary

table = {
    r"(\d+\.\d+)": "FLOAT",
    r"0x[0-9a-fA-F]+|0b(0|1[01]*)|\d+": "NUMBER",
    r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'': "STRING",
    r"\(": "LPAREN",
    r"\)": "RPAREN",
    r":=": "ASSIGN",
    r";": "SEMICOLON",
    r":": "COLON",
    r"\]": "CLOSED_BRACKETS",
    r"\[": "OPEN_BRACKETS",
    r"\{": "BEGIN",  # Sequence Begin
    r"\}": "END",  # Sequence End
    r"->": "LAMBDA_ARROW",
    r"\.\.\.": "DOTS",
    r"\.\.": "ITER",
    r"\.": "DOT",
    "wenn": "IF",
    "gilt,": "THEN",
    ",aber": "ELIF",
    "sonst": "ELSE",
    "solange": "WHILE",
    "für": "LOOP",
    "wiederhole": "LOOPTHEN",
    "in": "IN",
    "lambda": "LAMBDA",
    "echo": "PRINT",
    "importiere": "IMPORT",
    # "match": "MATCH",
    "vergleiche": "MATCH",
    "mit": "WITH",
    "fall": "CASE",
    "struct": "STRUCT",
    "&": "CONS",
    "leere": "NULL",
    "sei": "LET",  # Ist schon ein Letrec
    r",": "COMMA",
}
assigns = {k + ":=": v + "_ASSIGN" for k, v in binops.items()}
table.update(assigns)
table.update(binops)
table.update(unary)
table.update(
    {
        r"(?:[^\W\d_]|[\U0001F300-\U0001FAFF_])(?:[^\W_]|[\d_]|[\U0001F300-\U0001FAFF])*": "IDENTIFIER"
    }
)
tokens = list(table.values())


for rule, func_name in table.items():
    rule_lexer(rule, func_name)

t_ignore = " \t"
t_ignore_comment = r"\#[^\#]*\#"


def t_newline(t):
    r"\n+"
    t.lineno += 1


########### TRACEBACK #########
def print_traceback(input_text: str, token):
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

    print(f"SyntaxError: Unerwartetes Token '{token.value}' ({token.type}) in Zeile {line_num}, Spalte {col + 1}:")
    print(f"    {line}")
    print(f"    {' ' * col}^")


def t_error(t):
    print_traceback(t.lexer.lexdata, t)
    t.lexer.skip(1)
    return t


lexer: Lexer = lex()

if __name__ == "__main__":
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
