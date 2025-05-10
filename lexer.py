from ply.lex import Lexer, lex

operations = ["PLUS", "MINUS", "TIMES", "DIVIDE_CEIL", "DIVIDE_FLOOR", "DIVIDE"]
comparators = [
    "GREATER_THAN",
    "SMALLER_THAN",
    "UNEQUALS",
    "EQUALS",
    "SMALLER_EQUALS",
    "GREATER_EQUALS",
]

keywords = {
    "and": "AND",
    "or": "OR",
    "xor": "XOR",
    "not": "NOT",
    "mod": "MOD",
    "e": "EXP",  # als Operator
    "imag": "IMAG",  # als Operator
}

tokens = (
    [
        "NUMBER",
        "FLOAT",
        "IDENTIFIER",
        "LPAREN",
        "RPAREN",
        "ASSIGN",
        "SEMICOLON",
        "BEGIN",  # Sequence Begin
        "END",  # Sequence End
    ]
    + operations
    + comparators
    + list(keywords.values())
)

t_LPAREN = r"\("
t_RPAREN = r"\)"
t_ASSIGN = r":="

t_PLUS = r"\+"
t_MINUS = r"-"
t_TIMES = r"\*"
t_DIVIDE_CEIL = r"/"
t_DIVIDE = r"\|"
t_DIVIDE_FLOOR = r"\\"

t_GREATER_THAN = r">"
t_SMALLER_THAN = r"<"
t_UNEQUALS = r"!="
t_EQUALS = r"="
t_GREATER_EQUALS = r">="
t_SMALLER_EQUALS = r"<="

t_SEMICOLON = r";"
t_BEGIN = r"\{"
t_END = r"\}"

t_ignore = " \t"
t_ignore_comment = r"\#[^\#]*\#"


def t_FLOAT(t):
    r"(\d+\.\d*|\.\d+)"
    return t


def t_NUMBER(t):
    r"0x[0-9a-fA-F]+|0b(0|1[01]*)|\d+"
    return t


def t_IDENTIFIER(t):
    r"(?:[^\W\d_]|[\U0001F300-\U0001FAFF_])(?:[^\W_]|[\d_]|[\U0001F300-\U0001FAFF])*"
    # ?:[^\W\d_] : ein Zeichen, das ein Buchstabe ist, aber keine Ziffer und kein Unterstrich.
    # [\U0001F300-\U0001FAFF_] : Unicode-Zeichen im Bereich von U+1F300 bis U+1FAFF (Emoji- und Symbolbereich) oder der Unterstrich (_)
    #
    # ?:[^\W_]|[\d_] : Ein Buchstabe oder eine Ziffer (ohne Unterstrich) oder eine Ziffer oder ein Unterstrich
    # [\U0001F300-\U0001FAFF_] : Unicode-Zeichen im Bereich von U+1F300 bis U+1FAFF (Emoji- und Symbolbereich) oder der Unterstrich (_)
    # beliebig oft wiederholt
    t.type = keywords.get(t.value.lower(), "IDENTIFIER")
    return t


def t_newline(t):
    r"\n+"
    t.lexer.lineno += len(t.value)


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


def t_error(t):
    print_error_with_caret(t.lexer.lexdata, t.lineno, t.lexpos)
    t.lexer.skip(1)


lexer: Lexer = lex()

if __name__ == "__main__":
    # Eigene Cases
    lexer.input(r"name_von_😆_😎 := ((3 / 5)+1)|2\2")
    print(lexer.lexdata)
    for token in lexer:
        print(token)
    lexer.input(r"25/(3*40) + (300-20) -16.5")
    print(lexer.lexdata)
    for token in lexer:
        print(token)
    lexer.input(r"(300-250)<(400-500)")
    print(lexer.lexdata)
    for token in lexer:
        print(token)
    lexer.input(r"20 and 30 or 50")
    print(lexer.lexdata)
    for token in lexer:
        print(token)
    lexer.input(r"x0 mod 5 \ 4 e 10 ** 4 | 2 + 3 / 5")
    print(lexer.lexdata)
    for token in lexer:
        print(token)

    code = r"""
    x := 0xff + 0b11 - 5 e 10
    #
    Kommentar
    #
    + 3
    """
    lexer.input(code)
    for tok in lexer:
        print(tok)

    # Commandzeile
    lexer.input(input())
    for token in lexer:
        print(token)
