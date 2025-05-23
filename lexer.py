from ply.lex import Lexer, lex

operations = [
    "PLUS",
    "MINUS",
    "TIMES",
    "POWER",
    "DIVIDE_CEIL",
    "DIVIDE_FLOOR",
    "DIVIDE",
]
comparators = [
    "GREATER_THAN",
    "SMALLER_THAN",
    "UNEQUALS",
    "EQUALS",
    "SMALLER_EQUALS",
    "GREATER_EQUALS",
]

assigns = [i + "ASSIGN" for i in operations + comparators]

keywords = {
    "and": "AND",
    "or": "OR",
    "xor": "XOR",
    "mod": "MOD",
    "e": "EXP",  # als Operator
    "not": "NOT",
    "imag": "IMAG",  # als Operator
    "wenn": "IF",
    "gilt,": "THEN",
    ",aber": "ELIF",
    "sonst": "ELSE",
    "solange": "WHILE",
    "für": "LOOP",
    "wiederhole": "LOOPTHEN",
    "in": "LOOPIN",
    "lambda": "LAMBDA",
    "echo": "ECHO",
    "länge": "LENGTH",
}

assigns += [x + "ASSIGN" for x in ["AND", "OR", "XOR", "MOD", "EXP"]]


tokens = (
    [
        "NUMBER",
        "FLOAT",
        "IDENTIFIER",
        "LPAREN",
        "RPAREN",
        "ASSIGN",
        "SEMICOLON",
        "COMMA",
        "COLON",
        "CLOSED_BRACKETS",
        "OPEN_BRACKETS",
        "BEGIN",  # Sequence Begin
        "END",  # Sequence End
        "LAMBDA_ARROW",
        "ENDCOND",
        "DOTS",
    ]
    + operations
    + comparators
    + list(keywords.values())
    + assigns
)

t_PLUS = r"\+"
t_MINUS = r"-"
t_TIMES = r"\*"
t_POWER = r"\*\*"
t_DIVIDE_CEIL = r"/"
t_DIVIDE = r"\|"
t_DIVIDE_FLOOR = r"\\"
t_GREATER_THAN = r">"
t_SMALLER_THAN = r"<"
t_UNEQUALS = r"!="
t_EQUALS = r"="
t_GREATER_EQUALS = r">="
t_SMALLER_EQUALS = r"<="

t_PLUSASSIGN = r"\+:="
t_MINUSASSIGN = r"-:="
t_TIMESASSIGN = r"\*:="
t_POWERASSIGN = r"\*\*:="
t_DIVIDE_CEILASSIGN = r"/:="
t_DIVIDEASSIGN = r"\|:="
t_DIVIDE_FLOORASSIGN = r"\\:="
t_GREATER_THANASSIGN = r">:="
t_SMALLER_THANASSIGN = r"<:="
t_UNEQUALSASSIGN = r"!=:="
t_EQUALSASSIGN = r"=:="
t_GREATER_EQUALSASSIGN = r">=:="
t_SMALLER_EQUALSASSIGN = r"<=:="

t_LPAREN = r"\("
t_RPAREN = r"\)"
t_ASSIGN = r":="

t_SEMICOLON = r";"
t_BEGIN = r"\{"
t_END = r"\}"
t_CLOSED_BRACKETS = r"\]"
t_OPEN_BRACKETS = r"\["
t_COMMA = r"\,"

t_COLON = r"\:"
t_LAMBDA_ARROW = r"->"

t_ignore = " \t"
t_ignore_comment = r"\#[^\#]*\#"


def t_FLOAT(t):
    r"(\d+\.\d*|\.\d+)"
    return t


def t_NUMBER(t):
    r"0x[0-9a-fA-F]+|0b(0|1[01]*)|\d+"
    return t


def t_MODASSIGN(t):
    r"mod:="
    return t


def t_ANDASSIGN(t):
    r"and:="
    return t


def t_ORASSIGN(t):
    r"or:="
    return t


def t_XORASSIGN(t):
    r"xor:="
    return t


def t_DOTS(t):
    r"\.\.\."
    return t


def t_ENDCOND(t):
    r"\."
    return t


def t_THEN(t):
    r"gilt,"
    return t


def t_ELIF(t):
    r",aber"
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
