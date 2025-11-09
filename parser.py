from utils import generator
from ply.yacc import yacc
from lexer import tokens, op_assigns, print_traceback
from environment import SymbolTable

unique = generator()
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
    "imag": "imag",
}


# FUNCTION DEFINITION
EXPR = "expr"


class Node:

    def __init__(self, tag: str, *args):
        self.ast = (tag, *args)
        self.sym: SymbolTable
        self.code: list
        self.ty: str
        self.free: set

    def __iter__(self):
        return iter(self.ast)

    def __getitem__(self, key):
        return self.ast[key]

    def __repr__(self):
        return f"{self.ast}"


def print_ast(node: Node, level=0):
    indent = "  " * level
    match node.ast:
        case "num" | "float" | "str" | "var", value:
            print(f"{indent}{node.ast[0]}: {value}")
        case "program", body:
            print(f"{indent}program:")
            print_ast(body, level + 1)
        case "binop", op, lhs, rhs:
            print(f"{indent}binop: {op}")
            print_ast(lhs, level + 1)
            print_ast(rhs, level + 1)
        case "unary", op, expr:
            print(f"{indent}unary: {op}")
            print_ast(expr, level + 1)
        case "seq", body:
            print(f"{indent}seq:")
            for expr in body:
                print_ast(expr, level + 1)
        case "assign", ty, name, expr:
            print(f"{indent}assign: {name} of type {ty}")
            print_ast(expr, level + 1)
        case "comparison", *args:
            print(f"{indent}comparison:")
            for i in range(0, len(args[0]), 1):
                if i > 0:
                    print(f"{indent}  op: {args[0][i]}")
                print_ast(args[1][i], level + 1)
        case "if", condition, cond_body, else_if:
            print(f"{indent}if:")
            print(f"{indent}  condition:")
            print_ast(condition, level + 2)
            print(f"{indent}  then:")
            print_ast(cond_body, level + 2)
            if else_if:
                print(f"{indent}  else:")
                for case, body in else_if:
                    if case == "else":
                        print(f"{indent}    else:")
                        print_ast(body, level + 3)
                    else:
                        print(f"{indent}    elif condition:")
                        print_ast(case, level + 3)
                        print(f"{indent}    then:")
                        print_ast(body, level + 3)
        case "while", cond, body:
            print(f"{indent}while:")
            print(f"{indent}  condition:")
            print_ast(cond, level + 2)
            print(f"{indent}  body:")
            print_ast(body, level + 2)
        case "loop", id, iterator, body:
            print(f"{indent}loop {id} in:")
            print_ast(iterator, level + 2)
            print(f"{indent}  body:")
            print_ast(body, level + 2)
        case _:
            print(f"{indent}{node.ast[0]}:")
    print(node.sym)


def rule_f(name, rule, func):
    def f(p):
        p[0] = func(p)

    f.__doc__ = rule
    setattr(module, unique(f"p_{name}"), f)


def rule_n(tag, rule, **children):
    def f(p):
        c = (
            p[value] if isinstance(value, int) else value
            for _, value in children.items()
        )
        return Node(tag, *c)

    rule_f(tag, rule, f)


def node_b(op, prec=None):
    rule_f(
        EXPR,
        f"{EXPR} : {EXPR} {op} {EXPR} %prec {prec if prec else op}",
        lambda p: Node("binop", look_up_table[p[2]], p[1], p[3]),
    )


def node_u(op, postfix=False, prec=None):
    op_pos = 2 if postfix else 1
    rule = f"{EXPR} {op}" if postfix else f"{op} {EXPR}"

    rule_f(
        EXPR,
        f"{EXPR} : {rule} %prec {prec if prec else op}",
        lambda p: Node("unary", unary[p[op_pos]], p[3 - op_pos]),
    )


def rule_l(name, elem, sep, trailing_seperator="disallow"):
    rule_f(name, f"{name} : {elem} {sep} {name}", lambda p: [p[1], *p[3]])

    # trailing_seperator == 'allow' does both
    if trailing_seperator != "disallow":
        rule_f(name, f"{name} : {elem} {sep}", lambda p: [p[1]])

    if trailing_seperator != "force":
        rule_f(name, f"{name} : {elem}", lambda p: [p[1]])


# FUNCTION DEFINITION END


######################## ATOMIC #########################
rule_n("num", "expr : NUMBER", val=1)
rule_n("float", "expr : FLOAT", val=1)
rule_n("str", "expr : STRING", val=1)
rule_n("var", "expr : IDENTIFIER", name=1)
rule_f("paren", "expr : LPAREN expr RPAREN", lambda p: p[2])

######################## BINOP #########################
node_b("PLUS")
node_b("MINUS")
node_b("POWER")
node_b("TIMES")
node_b("DIVIDE_CEIL")
node_b("DIVIDE_FLOOR")
node_b("DIVIDE")
node_b("AND")
node_b("XOR")
node_b("OR")
node_b("EXP")
node_b("MOD")

######################## UNARY #########################
node_u("NOT")
node_u("PLUS", prec="UPLUS")
node_u("MINUS", prec="UMINUS")
node_u("IMAG", postfix=True)

######################## COMPARATOR #########################
for op in [
    "EQUALS",
    "UNEQUALS",
    "GREATER_THAN",
    "SMALLER_THAN",
    "SMALLER_EQUALS",
    "GREATER_EQUALS",
]:
    rule_f(
        "comp",
        f"comp : expr {op} expr %prec CMP",
        lambda p: [look_up_table[p[2]], p[1], p[3]],
    )
    rule_f(
        "comp",
        f"comp : comp {op} expr %prec CMP2",
        lambda p: [p[1][0] + [look_up_table[p[2]]], p[1][1] + [p[3]]],
    )

rule_f("expr", "expr : comp %prec CLS", lambda p: Node("comparison", *p[1]))

######################## ASSIGNMENTS #########################
rule_f("type", "type : T_INT", lambda _: "i64")
rule_f("type", "type : T_FLOAT", lambda _: "f64")
rule_f("type", "type : T_STRING", lambda _: "str")
rule_f("type", "type : T_COMPLEX", lambda _: "c64")
rule_l("type_arg", "type", "COMMA", trailing_seperator="disallow")
rule_f("type", "type : LPAREN type_arg RPAREN ARROW type", lambda p: ("->", p[2], p[5]))
rule_f("type", "type : type ARROW type", lambda p: ("->", [p[1]], p[3]))
rule_f("type", "type : OPEN_BRACKETS CLOSED_BRACKETS type", lambda p: "[]" + p[3])

rule_f(
    "assign_expr",
    "assign_expr : type IDENTIFIER ASSIGN expr",
    lambda p: Node("assign", p[1], p[2], p[4]),
)
rule_f(
    "assign_expr",
    "assign_expr : IDENTIFIER ASSIGN expr",
    lambda p: Node("assign", None, p[1], p[3]),
)
rule_f("expr", "expr : assign_expr", lambda p: p[1])

for op in op_assigns:
    rule_f(
        "assign",
        f"expr : IDENTIFIER {op} expr",
        lambda p: Node(
            "assign",
            None,
            p[1],
            Node("binop", look_up_table[p[2][:-2]], Node("var", p[1]), p[3]),
        ),
    )

rule_n("undef", "expr : T_UNDEF expr", expr=2)

##################### PROGRAM #########################
rule_n("program", "program : expr", expr=1)

##################### SEQUENCE #########################
rule_l("sequence", "expr", "SEMICOLON", trailing_seperator="allow")
rule_f("expr", "expr : BEGIN sequence END", lambda p: Node("seq", p[2]))
rule_f("expr", "expr : BEGIN END", lambda _: Node("seq", []))

######################## ITE #########################
rule_n(
    "if", "expr : IF expr THEN COMMA expr DOT", condition=2, cond_body=5, else_if=None
)
rule_n(
    "if",
    "expr : IF expr THEN COMMA expr else_elif_body DOT",
    condition=2,
    cond_body=5,
    else_if=6,
)

rule_f(
    "else",
    "else_elif_body : COMMA ELIF IF expr THEN COMMA expr else_elif_body",
    lambda p: [(p[4], p[7]), *p[8]],
)
rule_f("else", "else_elif_body : ELSE expr", lambda p: [("else", p[2])])

rule_f(
    "elif",
    "else_elif_body : COMMA ELIF IF expr THEN COMMA expr",
    lambda p: [(p[4], p[7])],
)

######################## WHILE #########################
rule_n("while", "expr : WHILE expr THEN COMMA expr DOT", cond=2, body=5)

######################## LOOP #########################
rule_n(
    "loop",
    "expr : LOOP IDENTIFIER IN expr LOOPTHEN expr DOT",
    id=2,
    iterator=4,
    body=6,
)
for op, op2 in [
    ("OPEN_BRACKETS", "CLOSED_BRACKETS"),
    ("CLOSED_BRACKETS", "CLOSED_BRACKETS"),
    ("OPEN_BRACKETS", "OPEN_BRACKETS"),
    ("CLOSED_BRACKETS", "OPEN_BRACKETS"),
]:
    rule_n(
        "interval",
        f"expr : {op} expr DOT DOT expr {op2}",
        lbr=1,
        a=2,
        b=5,
        rbr=6,
    )

######################## LAMBDA #########################
rule_n(
    "lambda",
    "expr : LAMBDA para ARROW type COLON expr %prec LAMBDA",
    para=2,
    body=6,
    ty=4,
)
rule_n("call", "expr : expr LPAREN para_expr RPAREN", func=1, para=3)
rule_f("empty", "empty :", lambda _: [])
rule_f(
    "para",
    "para : LPAREN param_pos RPAREN",
    lambda p: p[2],
)
rule_f("para", "para : type IDENTIFIER", lambda p: [("pos", p[1], p[2])])
rule_f("para", "para : IDENTIFIER", lambda p: [("pos", None, p[1])])
rule_f("para", "para : empty", lambda _: [])

rule_f("param_pos", "param_pos : param_pos_list", lambda p: p[1])
rule_f(
    "param_pos_list",
    "param_pos_list : type IDENTIFIER COMMA param_pos_list",
    lambda p: [("pos", p[1], p[2]), *p[4]],
)
rule_f(
    "param_pos_list",
    "param_pos_list : type IDENTIFIER",
    lambda p: [("pos", p[1], p[2])],
)
rule_f(
    "param_pos_list",
    "param_pos_list : IDENTIFIER COMMA param_pos_list",
    lambda p: [("pos", None, p[1]), *p[3]],
)
rule_f("param_pos_list", "param_pos_list : IDENTIFIER", lambda p: [("pos", None, p[1])])
rule_f("param_pos_list", "param_pos_list : para_keywords", lambda p: p[1])
rule_f("para_keywords", "para_keywords : para_kw_list", lambda p: p[1])
rule_f(
    "para_kw_list",
    "para_kw_list : type IDENTIFIER COLON expr COMMA para_kw_list",
    lambda p: [("keyword", p[1], p[2], p[4]), *p[6]],
)
rule_f(
    "para_kw_list",
    "para_kw_list : IDENTIFIER COLON expr COMMA para_kw_list",
    lambda p: [("keyword", None, p[1], p[3]), *p[5]],
)
rule_f(
    "para_kw_list",
    "para_kw_list : type IDENTIFIER COLON expr",
    lambda p: [("keyword", p[1], p[2], p[4])],
)
rule_f(
    "para_kw_list",
    "para_kw_list : IDENTIFIER COLON expr",
    lambda p: [("keyword", None, p[1], p[3])],
)
rule_f("para_kw_list", "para_kw_list : para_infty", lambda p: p[1])
rule_f(
    "para_infty",
    "para_infty : IDENTIFIER DOT DOT DOT",
    lambda p: [("infty", None, p[1])],
)
rule_f("para_expr", "para_expr : param_pos_expr", lambda p: p[1])
rule_f("para_expr", "para_expr : empty", lambda p: p[1])
rule_f(
    "param_pos_expr",
    "param_pos_expr : expr COMMA param_pos_expr",
    lambda p: [("pos", p[1]), *p[3]],
)
rule_f("param_pos_expr", "param_pos_expr : expr", lambda p: [("pos", p[1])])
rule_f("param_pos_expr", "param_pos_expr : para_keywords_expr", lambda p: p[1])
rule_f(
    "para_keywords_expr",
    "para_keywords_expr : expr COLON expr COMMA para_keywords_expr",
    lambda p: [("keyword", p[1], p[3]), *p[5]],
)
rule_f(
    "para_keywords_expr",
    "para_keywords_expr : expr COLON expr",
    lambda p: [("keyword", p[1], p[3])],
)

######################## LETREC #########################
rule_f(
    "letrec_assign",
    "letrec_assign : letrec_assign COMMA assign_expr",
    lambda p: p[1] + [p[3]],
)
rule_f("letrec_assign", "letrec_assign : assign_expr", lambda p: [p[1]])
rule_f(
    "expr",
    "expr : LET letrec_assign IN expr DOT",
    lambda p: Node("letrec", p[2], p[4]),
)

######################## LISTS #########################
rule_f("param_list", "param_list : param_list COMMA expr", lambda p: [*p[1], p[3]])
rule_f("param_list", "param_list : expr COMMA expr", lambda p: [p[1], p[3]])
rule_n("list", "expr : LPAREN param_list RPAREN", para=2)
rule_n(
    "array_access",
    "expr : expr OPEN_BRACKETS PLUS CLOSED_BRACKETS",
    array=1,
    index=3,
)
rule_n(
    "array_access",
    "expr : expr OPEN_BRACKETS expr CLOSED_BRACKETS",
    array=1,
    index=3,
)
rule_f("leere", "expr : NULL", lambda _: Node("leere"))
rule_n("cons", "expr : expr CONS expr", expr1=1, expr2=3)

######################## ARRAY #########################
rule_f(
    "expr",
    "expr : OPEN_BRACKETS param_list CLOSED_BRACKETS",
    lambda p: Node("array", p[2]),
)
rule_f(
    "expr", "expr : OPEN_BRACKETS expr CLOSED_BRACKETS", lambda p: Node("array", [p[2]])
)
rule_f("expr", "expr : OPEN_BRACKETS CLOSED_BRACKETS", lambda _: Node("array", []))

####################### STRUCTS ########################
rule_l("assign_list", "assign_expr", "SEMICOLON", trailing_seperator="disallow")
rule_f("expr", "expr : STRUCT BEGIN assign_list END", lambda p: Node("struct", p[3]))
rule_f("expr", "expr : STRUCT BEGIN END", lambda _: Node("struct", []))
rule_n("access_struct", "expr : expr ARROW expr", struct=1, name=3)

######################## IMPORT ########################
rule_f("file", "file : STRING", lambda p: [p[1][1:-1]])
rule_n("import", "expr : IMPORT file", file=2)

######################## MATCH #########################
rule_n("match", "expr : MATCH expr WITH cases DOT", expr=2, cases=4)
rule_f(
    "cases", "cases : CASE expr COLON expr DOT cases", lambda p: [(p[2], p[4]), *p[6]]
)
rule_f("cases", "cases : CASE expr COLON expr DOT", lambda p: [(p[2], p[4])])


########################################################


def p_error(p):
    if p:
        print_traceback(p.lexer.lexdata, p)
        print(f"Syntaxfehler bei Token '{p.value}' vom Typ {p.type}")
    else:
        print("Syntaxfehler: Unerwartetes Dateiende")


########################################################

precedence = (
    ("right", "ASSIGN", *op_assigns, "T_UNDEF"),
    ("right", "DOT"),
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
    (
        "left",
        "OPEN_BRACKETS",
        "CLOSED_BRACKETS",
        "LPAREN",
        "RPAREN",
        "BEGIN",
        "ARROW",
        "END",
    ),
)

########################################################

parser = yacc(start="program", debug=True, write_tables=True)

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
