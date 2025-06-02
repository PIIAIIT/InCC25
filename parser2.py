import unique_name
from ply.yacc import yacc
from lexer import tokens, binops, unary, assigns, print_error_with_caret

unique = unique_name.generator()
module = __import__(__name__)


def rule_func(name, rule, func):
    def f(p):
        p[0] = func(p)

    f.__doc__ = rule
    setattr(module, unique(f"p_{name}"), f)


def rule_node(tag, rule, **children):
    def f(p):
        c = (
            p[value] if isinstance(value, int) else value
            for _, value in children.items()
        )
        return (tag, *c)

    rule_func(tag, rule, f)


def node_binop(op, prec=None):
    rule_node(
        "binop",
        f"expression : expression {op} expression %prec {prec if prec else op}",
        operator=op,
        lhs=1,
        rhs=3,
    )


def node_unop(op, prec=None):
    rule_node(
        "unop",
        f"expression : {op} expression %prec {prec if prec else op}",
        operator=op,
        operand=2,
    )


def rule_list(name, elem, sep, trailing_seperator="disallow"):
    rule_func(name, f"{name} : {elem} {sep} {name}", lambda p: [p[1], *p[3]])

    # trailing_seperator == 'allow' does both
    if trailing_seperator != "disallow":
        rule_func(name, f"{name} : {elem} {sep}", lambda p: [p[1]])

    if trailing_seperator != "force":
        rule_func(name, f"{name} : {elem}", lambda p: [p[1]])


######################## ATOMIC #########################
rule_node("num", "atomar : NUMBER", val=1)
rule_node("float", "atomar : FLOAT", val=1)
rule_node("var", "atomar : IDENTIFIER", name=1)

######################## EXPRESSION #########################
rule_func("paren", "expression : LPAREN expression RPAREN", lambda p: p[2])

######################## BINOP #########################
for op in binops.values():
    node_binop(op)

######################## UNARY #########################
node_unop("NOT")
node_unop("IMAG")
node_unop("PLUS", prec="UPLUS")
node_unop("MINUS", prec="UMINUS")

######################## COMPARATOR #########################
for op in [
    "SMALLER_THAN",
    "GREATER_THAN",
    "SMALLER_EQUALS",
    "GREATER_EQUALS",
    "EQUALS",
    "UNEQUALS",
]:
    rule_list("comparison", "expression", op, trailing_seperator="allow")
    rule_node("comparison", f"expression : expression {op} expression", body=2)

######################## ASSIGNMENTS #########################
rule_node("assign", "expression : IDENTIFIER ASSIGN expression", op=None, id=1, expr=3)
for op in binops.items():
    rule_node(
        "assign", f"expression : IDENTIFIER {op}_ASSIGN expression", op=2, id=1, expr=3
    )

######################## SEQUENCE #########################
rule_list("sequence", "expression", "SEMICOLON", trailing_seperator="allow")
rule_node("sequence", "expression : BEGIN sequence END", body=2)

######################## ITE #########################

######################## WHILE #########################

######################## LOOP #########################

######################## LAMBDA #########################

######################## BUILTIN #########################

########################################################


def p_error(p):
    if p:
        print(f"Syntaxfehler bei Token '{p.value}' vom Typ {p.type}")
        print_error_with_caret(p.lexer.lexdata, p.lineno, p.lexpos)
    else:
        print("Syntaxfehler: Unerwartetes Dateiende")


########################################################

precedence = (
    tuple(["right", "ASSIGN"] + [a for a in assigns.values()]),
    ("right", "LAMBDA"),
    ("right", "CALL"),
    ("left", "OR"),
    ("left", "XOR"),
    ("left", "AND"),
    ("left", "EQUALS", "UNEQUALS"),
    (
        "left",
        "GREATER_THAN",
        "SMALLER_THAN",
        "SMALLER_EQUALS",
        "GREATER_EQUALS",
    ),
    ("left", "PLUS", "MINUS"),
    ("left", "TIMES", "DIVIDE", "DIVIDE_CEIL", "DIVIDE_FLOOR", "MOD"),
    ("right", "POWER", "EXP"),
    ("left", "IMAG"),
    ("right", "NOT", "UPLUS", "UMINUS"),  # weil -7++ = -6 und nicht -8
)

########################################################

parser = yacc(start="sequence")

if __name__ == "__main__":
    # Eigene Cases
    while True:
        try:
            s = input(">>> ")
        except EOFError:
            break

        if not s or s.lower() == "\n":
            continue
        if s.lower() == "q":
            break

        res = parser.parse("{" + s + "}", debug=False)
        print(res)
