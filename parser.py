from ply.yacc import yacc
from lexer import tokens, print_error_with_caret

look_up_table = {
    "+": "plus",
    "-": "minus",
    "*": "times",
    "/": "divide_ceil",
    "|": "divide",
    "mod": "mod",
    "\\": "divide_floor",
    "e": "exp",
    "imag": "imag",
    # booleans
    "and": "and",
    "or": "or",
    "xor": "xor",
    "=": "equals",
    ">": "greater_than",
    "<": "smaller_than",
    ">=": "greater_equals",
    "<=": "smaller_equals",
    "!=": "unequals",
}
deinc = {"++": "inc", "--": "dec"}
unary = {
    "not": "not",
    "-": "uminus",
    "+": "uplus",
}


def p_number(p):
    "atomar : NUMBER"
    p[0] = ("num", p[1])


def p_float(p):
    "atomar : FLOAT"
    p[0] = ("float", p[1])


def p_var(p):
    "atomar : IDENTIFIER"
    p[0] = ("var", p[1])


def p_paran(p):
    "atomar : LPAREN expression RPAREN"
    p[0] = p[2]


def p_expression(p):
    """expression : expression PLUS expression
    | expression MINUS expression
    | expression TIMES expression
    | expression DIVIDE expression
    | expression DIVIDE_CEIL expression
    | expression DIVIDE_FLOOR expression
    | expression MOD expression
    | expression EXP expression
    | expression AND expression
    | expression OR expression
    | expression XOR expression
    | expression GREATER_THAN   expression
    | expression SMALLER_THAN   expression
    | expression SMALLER_EQUALS expression
    | expression GREATER_EQUALS expression
    | expression EQUALS         expression
    | expression UNEQUALS    expression
    | atomar
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        op = look_up_table[p[2]]
        p[0] = ("binop", op, p[1], p[3])


def p_comp(p):
    """comparator : cmp expression"""
    p[0] = ([p[1]], [p[2]])


def p_cmp(p):
    """cmp : GREATER_THAN
    | SMALLER_THAN
    | SMALLER_EQUALS
    | GREATER_EQUALS
    | EQUALS
    | UNEQUALS"""
    p[0] = look_up_table[p[1]]


def p_compare_extr(p):
    "comparator : comparator comparator"
    [a, b], [c, d] = p[1], p[2]
    p[0] = (a + c, b + d)


def p_compare_exp(p):
    "expression : expression comparator"
    a, b = p[2]
    b.insert(0, p[1])
    p[0] = ("comp", a, b)


def p_expr_postfix(p):
    """expression : expression PLUS PLUS %prec POSTINC
    | expression MINUS MINUS %prec POSTDEC
    """
    p[0] = ("postfix", deinc[p[2] + p[3]], p[1])


def p_expr_power(p):
    "expression : expression TIMES TIMES expression %prec POWER"
    p[0] = ("power", p[1], p[4])


def p_unary(p):
    """expression : NOT expression
    | MINUS expression %prec UMINUS
    | PLUS expression %prec UPLUS"""
    p[0] = ("unary", unary[p[1]], p[2])


def p_complex(p):
    """expression : expression IMAG"""
    p[0] = ("complex", p[1])


def p_assign(p):
    "expression : IDENTIFIER ASSIGN expression"
    p[0] = ("assign", p[1], p[3])


def p_sequence(p):
    """
    sequence : BEGIN body END
             | BEGIN body SEMICOLON END
    """
    p[0] = ("seq", p[2])


def p_body1(p):
    """body : expression"""
    p[0] = [p[1]]


def p_body2(p):
    """body : body SEMICOLON expression"""
    p[0] = p[1] + [p[3]]


def p_error(p):
    if p:
        print(f"Syntaxfehler bei Token '{p.value}' vom Typ {p.type}")
        print_error_with_caret(p.lexer.lexdata, p.lineno, p.lexpos)
    else:
        print("Syntaxfehler: Unerwartetes Dateiende")


precedence = (
    ("right", "ASSIGN"),
    ("left", "OR"),
    ("left", "XOR"),
    ("left", "AND"),
    ("left", "EQUALS", "UNEQUALS"),
    (
        "nonassoc",
        "GREATER_THAN",
        "SMALLER_THAN",
        "SMALLER_EQUALS",
        "GREATER_EQUALS",
    ),
    ("left", "PLUS", "MINUS"),
    ("left", "TIMES", "DIVIDE", "DIVIDE_CEIL", "DIVIDE_FLOOR", "MOD"),
    ("right", "POWER", "EXP"),
    ("left", "POSTINC", "POSTDEC", "IMAG"),
    ("right", "NOT", "UPLUS", "UMINUS"),  # weil -7++ = -6 und nicht -8
)

parser = yacc(start="sequence")

if __name__ == "__main__":
    # Eigene Cases
    print("Please start the main File in test/")
    res = parser.parse("{" + input() + "}")
    print(res)
