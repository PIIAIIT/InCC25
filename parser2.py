import unique_name
from ply.yacc import yacc
from lexer import tokens, binops, op_assigns, print_traceback

unique = unique_name.generator()
module = __import__(__name__)

look_up_table = {
    "+": "plus",
    "-": "minus",
    "*": "times",
    "**": "power",
    "/": "divide_ceil",
    "|": "divide",
    "mod": "mod",
    "\\": "divide_floor",
    "e": "exp",
    "imag": "imag",
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
unary = {
    "not": "not",
    "-": "uminus",
    "+": "uplus",
}


# FUNCTION DEFINITION
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
    rule_func(
        "expression",
        f"expression : expression {op} expression %prec {prec if prec else op}",
        lambda p:
            ("binop", look_up_table[p[2]], p[1], p[3])
    )


def node_unop(op, postfix=False, prec=None):
    if postfix:
        rule_func(
            "expression",
            f"expression : expression {op} %prec {prec if prec else op}",
            lambda p:
                ("unary", unary[op], p[2])
        )
    else:
        rule_func(
            "expression",
            f"expression : {op} expression %prec {prec if prec else op}",
            lambda p:
                ("unary", unary[op], p[2])
        )


def rule_list(name, elem, sep, trailing_seperator="disallow"):
    rule_func(name, f"{name} : {elem} {sep} {name}", lambda p: [p[1], *p[3]])

    # trailing_seperator == 'allow' does both
    if trailing_seperator != "disallow":
        rule_func(name, f"{name} : {elem} {sep}", lambda p: [p[1]])

    if trailing_seperator != "force":
        rule_func(name, f"{name} : {elem}", lambda p: [p[1]])

# FUNCTION DEFINITION END


######################## ATOMIC #########################
rule_node("num",   "expression : NUMBER", val=1)
rule_node("float", "expression : FLOAT", val=1)
rule_node("str",   "expression : STRING", val=1)
rule_node("var",   "expression : IDENTIFIER", name=1)

######################## EXPRESSION #########################
rule_func("paren", "expression : LPAREN expression RPAREN", lambda p: p[2])

######################## BINOP #########################
for op in binops.values():
    node_binop(op)

######################## UNARY #########################
node_unop("NOT")
node_unop("PLUS", prec="UPLUS")
node_unop("MINUS", prec="UMINUS")
node_unop("IMAG", postfix=True)

######################## COMPARATOR #########################
rule_func(
    "comparison_op",
    """comparison_op : GREATER_THAN
                     | SMALLER_THAN
                     | UNEQUALS
                     | EQUALS
                     | SMALLER_EQUALS
                     | GREATER_EQUALS""",
    lambda p: look_up_table[p[1]]
)
rule_func(
    "comparison",
    "comparison : expression comparison_op expression %prec CMP",
    lambda p: [p[2], p[1], p[3]]
)

rule_func(
    "comparison",
    "comparison : comparison comparison_op expression %prec CMP2",
    lambda p: [p[1][0] + [p[2]], p[1][1] + [p[3]]]
)

rule_func(
    "expression",
    "expression : comparison %prec CLS",
    lambda p: ("comparison", *p[1])
)

######################## ASSIGNMENTS #########################
rule_func("assign_expression", "assign_expression : IDENTIFIER ASSIGN expression", lambda p: ("assign", None, p[1], p[3]))
rule_func("expression", "expression : assign_expression", lambda p: p[1])

for _, op in op_assigns.items():
    rule_func("assign", f"expression : IDENTIFIER {op} expression", lambda p: ("assign", look_up_table[p[2][:-2]], p[1], p[3]))


######################## SEQUENCE #########################
rule_list("expression", "expression", "SEMICOLON", trailing_seperator="allow")
rule_func("expression", "expression : BEGIN END", lambda p: ("seq", []))

######################## ITE #########################
rule_node("if", "expression : IF expression THEN COMMA expression DOT", condition=2, cond_body=5, else_if=None)
rule_node("if", "expression : IF expression THEN COMMA expression else_elif_body DOT", condition=2, cond_body=5, else_if=6)

rule_func("else", "else_elif_body : COMMA ELIF IF expression THEN COMMA expression else_elif_body", lambda p: [(p[4], p[7]), *p[8]])
rule_func("else", "else_elif_body : ELSE expression", lambda p: [("else", p[2])])

rule_func("elif", "else_elif_body : COMMA ELIF IF expression THEN COMMA expression", lambda p: [(p[4], p[7])])

######################## WHILE #########################
rule_node("while", "expression : WHILE expression THEN COMMA expression DOT", cond=2, body=5)

######################## LOOP #########################
rule_node("loop", "expression : LOOP IDENTIFIER IN expression LOOPTHEN expression DOT", id=2, iterator=4, body=6)
for op, op2 in [("OPEN_BRACKETS", "CLOSED_BRACKETS"),
                ("CLOSED_BRACKETS", "CLOSED_BRACKETS"),
                ("OPEN_BRACKETS", "OPEN_BRACKETS"),
                ("CLOSED_BRACKETS", "OPEN_BRACKETS")]:
    rule_node("interval", f"expression : {op} expression ITER expression {op2}", lbr=1, a=2, b=4, rbr=5)

######################## LAMBDA #########################
rule_node("lambda", "expression : LAMBDA parameter LAMBDA_ARROW expression %prec LAMBDA", parameter=2, body=4)

rule_node("call", "expression : expression LPAREN parameter_expr RPAREN", func=1, parameter=3)

rule_func("empty", "empty :", lambda p: [])
rule_func("parameter", "parameter : LPAREN parameter_pos RPAREN", lambda p: ("parameter", p[2]))
rule_func("parameter", "parameter : IDENTIFIER", lambda p: ("parameter", [("pos", p[1])]))
rule_func("parameter", "parameter : empty", lambda p: ("parameter", []))
rule_func("parameter_pos", "parameter_pos : parameter_entry", lambda p: p[1])
rule_list("parameter_entry", "parameter_entry", "COMMA", trailing_seperator="disallow")
rule_func("parameter_entry", "parameter_entry : IDENTIFIER COLON expression", lambda p: ("keyword", p[1], p[3]))
rule_func("parameter_entry", "parameter_entry : IDENTIFIER DOTS", lambda p: ("infty", p[1]))
rule_func("parameter_entry", "parameter_entry : IDENTIFIER", lambda p: ("pos", p[1]))

rule_func("parameter_expr", "parameter_expr : parameter_pos_expr", lambda p: ("parameter_expr", p[1]))
rule_func("parameter_expr", "parameter_expr : empty", lambda p: ("parameter_expr", []))
rule_func("parameter_pos_expr", "parameter_pos_expr : expression COMMA parameter_pos_expr", lambda p: [("pos", p[1]), *p[3]])
rule_func("parameter_pos_expr", "parameter_pos_expr : expression", lambda p: [("pos", p[1])])
rule_func("parameter_pos_expr", "parameter_pos_expr : parameter_keywords_expr", lambda p: p[1])
rule_func("parameter_keywords_expr", "parameter_keywords_expr : expression COLON expression COMMA parameter_keywords_expr", lambda p: [("keyword", p[1], p[3]), *p[5]])
rule_func("parameter_keywords_expr", "parameter_keywords_expr : expression COLON expression", lambda p: [("keyword", p[1], p[3])])

######################## LETREC #########################
rule_func("let_assign", "let_assign : IDENTIFIER EQUALS expression COMMA let_assign", lambda p: [("assign", None, p[1], p[3]), *p[5]])
rule_func("let_assign", "let_assign : IDENTIFIER EQUALS expression", lambda p: [("assign", None, p[1], p[3])])
rule_func("expression", "expression : LET let_assign IN expression DOT", lambda p: ("let", p[2], p[4]))

######################## LISTS #########################
rule_list("param_list", "expression", "COMMA", trailing_seperator="disallow")
rule_node("list", "expression : LPAREN param_list RPAREN", parameter=2)
rule_node("array_access", "expression : expression OPEN_BRACKETS PLUS CLOSED_BRACKETS", array=1, index=3)
rule_node("array_access", "expression : expression OPEN_BRACKETS expression CLOSED_BRACKETS", array=1, index=3)
rule_func("leere", "expression : NULL", lambda _ : ("leere"))
rule_node("cons", "expression : expression CONS expression", expr1=1, expr2=3)

######################## ARRAY #########################
rule_func("expression", "expression : OPEN_BRACKETS param_list CLOSED_BRACKETS", lambda p: ("array", p[2]))
rule_func("expression", "expression : OPEN_BRACKETS expression CLOSED_BRACKETS", lambda p : ("array", [p[2]]))
rule_func("expression", "expression : OPEN_BRACKETS CLOSED_BRACKETS", lambda p : ("array", []))

####################### STRUCTS ########################
rule_list("assignment_list", "assign_expression", "SEMICOLON", trailing_seperator="disallow")

rule_func("expression", "expression : STRUCT BEGIN assignment_list END", lambda p: ("struct", p[3]))
rule_func("expression", "expression : STRUCT BEGIN assign_expression END", lambda p: ("struct", [p[3]]))
rule_func("expression", "expression : STRUCT BEGIN END", lambda _: ("struct", []))

rule_node("access_struct", "expression : expression LAMBDA_ARROW expression", struct=1, name=3)

######################## IMPORT ########################
rule_func("file", "file : STRING", lambda p: [p[1][1:-1]])
rule_node("import", "expression : IMPORT file", file=2)

######################## MATCH #########################
rule_node("match", "expression : MATCH expression WITH cases DOT", expr=2, cases=4)
rule_func("cases", "cases : CASE expression COLON expression DOT cases", lambda p: [(p[2], p[4]), *p[6]])
rule_func("cases", "cases : CASE expression COLON expression DOT", lambda p: [(p[2], p[4])])


########################################################


def p_error(p):
    if p:
        print_traceback(p.lexer.lexdata, p)
        print(f"Syntaxfehler bei Token '{p.value}' vom Typ {p.type}")
    else:
        print("Syntaxfehler: Unerwartetes Dateiende")


########################################################

precedence = (
    ("right", "ASSIGN", *(a for a in op_assigns.values())),
    ("left", "LAMBDA"),
    ("left", "OR"),
    ("left", "XOR"),
    ("left", "AND"),
    ("left", "CLS", "CMP", "CMP2"),
    (
        "left",
        "EQUALS",
        "UNEQUALS",
        "GREATER_THAN",
        "SMALLER_THAN",
        "SMALLER_EQUALS",
        "GREATER_EQUALS",
    ),
    ("left", "PLUS", "MINUS"),
    ("left", "TIMES", "DIVIDE", "DIVIDE_CEIL", "DIVIDE_FLOOR", "MOD"),
    ("right", "POWER", "EXP"),
    ("left", "IMAG"),
    ("right", "NOT", "UPLUS", "UMINUS"),
    ("left", "CONS"),
    ("left", "OPEN_BRACKETS", "CLOSED_BRACKETS", "LPAREN", "RPAREN", "BEGIN", "LAMBDA_ARROW", "END"),
)

########################################################

parser = yacc(start="expression", debug=True, write_tables=True)

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
