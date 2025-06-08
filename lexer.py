from ply.lex import Lexer, lex

module = __import__(__name__)


def rule_lexer(doc, name):
    def f(t):
        return t

    f.__doc__ = doc
    setattr(module, f"t_{name.upper()}", f)


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
    "e": "EXP",  # als Operator
}
unary = {
    "not": "NOT",
    "imag": "IMAG",
}  # unary

table = {
    r"(\d+\.\d*|\.\d+)": "FLOAT",
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
    "echo": "ECHO",
    "länge": "LENGTH",
    "list": "LIST",
    "&": "CONST",
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


def print_error_with_caret(text, lineno, lexpos):
    # Zeile ermitteln
    lines = text.split("\n")
    if lineno - 1 >= len(lines):
        print("Ungültige Zeilennummer.")
        return

    error_line = lines[lineno - 1]

    # Position in Zeile berechnen
    line_start = sum(len(line) + 1 for line in lines[: lineno - 1])  # +1 für \n
    column = max(0, lexpos - line_start)

    # Ausgabe mit ^ unter dem Fehler
    print(f"Syntaxfehler in Zeile {lineno}:")
    print(error_line)
    print(" " * column + "^")


t_ignore = " \t"
t_ignore_comment = r"\#[^\#]*\#"


def t_newline(t):
    r"\n+"
    t.lineno += 1


def t_error(t):
    print_error_with_caret(t.lexer.lexdata, t.lineno, t.lexpos)
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
