from ply.yacc import yacc
from lexer import tokens, print_error_with_caret, assigns

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
look_up_table2 = {}
for k, v in look_up_table.items():
    look_up_table2[k + ":="] = v
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
    "arithmetic_expression : LPAREN arithmetic_expression RPAREN"
    p[0] = p[2]


def p_expression(p):
    """arithmetic_expression : arithmetic_expression PLUS arithmetic_expression
    | arithmetic_expression MINUS arithmetic_expression
    | arithmetic_expression TIMES arithmetic_expression
    | arithmetic_expression DIVIDE arithmetic_expression
    | arithmetic_expression DIVIDE_CEIL arithmetic_expression
    | arithmetic_expression DIVIDE_FLOOR arithmetic_expression
    | arithmetic_expression MOD arithmetic_expression
    | arithmetic_expression EXP arithmetic_expression
    | arithmetic_expression AND arithmetic_expression
    | arithmetic_expression OR arithmetic_expression
    | arithmetic_expression XOR arithmetic_expression
    | arithmetic_expression POWER arithmetic_expression
    | atomar
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        op = look_up_table[p[2]]
        p[0] = ("binop", op, p[1], p[3])


def p_unary(p):
    """arithmetic_expression : NOT arithmetic_expression
    | MINUS arithmetic_expression %prec UMINUS
    | PLUS arithmetic_expression %prec UPLUS"""
    p[0] = ("unary", unary[p[1]], p[2])


def p_complex(p):
    """expression : arithmetic_expression IMAG"""
    p[0] = ("complex", p[1])


def p_expression_comparison_chain1(p):
    """
    expression : arithmetic_expression comparison_op arithmetic_expression comparison_chain
    """
    p[0] = ("comparison_chain", p[1], [(p[2], p[3])] + p[4])


def p_expression_comparison_chain2(p):
    """
    expression : arithmetic_expression comparison_op arithmetic_expression
    """
    p[0] = ("comparison_chain", p[2], p[1], p[3])


def p_comparison_chain1(p):
    """
    comparison_chain : comparison_op arithmetic_expression comparison_chain
    """
    p[0] = [(p[1], p[2])] + p[3]


def p_comparison_chain2(p):
    """
    comparison_chain : comparison_op arithmetic_expression
    """
    p[0] = [(p[1], p[2])]


def p_comparison_op(p):
    """comparison_op : GREATER_THAN
    | SMALLER_THAN
    | UNEQUALS
    | EQUALS
    | SMALLER_EQUALS
    | GREATER_EQUALS"""
    p[0] = look_up_table[p[1]]


def p_assignment1(p):
    """expression : IDENTIFIER ASSIGN expression
    | IDENTIFIER ASSIGN arithmetic_expression"""
    p[0] = ("assign", p[1], p[3])


def p_assignment2(p):
    """
    expression : IDENTIFIER PLUSASSIGN expression
               | IDENTIFIER MINUSASSIGN expression
               | IDENTIFIER TIMESASSIGN expression
               | IDENTIFIER POWERASSIGN expression
               | IDENTIFIER DIVIDEASSIGN expression
               | IDENTIFIER DIVIDE_FLOORASSIGN expression
               | IDENTIFIER DIVIDE_CEILASSIGN expression
               | IDENTIFIER GREATER_THANASSIGN expression
               | IDENTIFIER SMALLER_THANASSIGN expression
               | IDENTIFIER GREATER_EQUALSASSIGN expression
               | IDENTIFIER SMALLER_EQUALSASSIGN expression
               | IDENTIFIER EQUALSASSIGN expression
               | IDENTIFIER UNEQUALSASSIGN expression
               | IDENTIFIER ANDASSIGN expression
               | IDENTIFIER ORASSIGN expression
               | IDENTIFIER XORASSIGN expression
               | IDENTIFIER EXPASSIGN expression
               | IDENTIFIER MODASSIGN expression
               | IDENTIFIER PLUSASSIGN arithmetic_expression
               | IDENTIFIER MINUSASSIGN arithmetic_expression
               | IDENTIFIER TIMESASSIGN arithmetic_expression
               | IDENTIFIER POWERASSIGN arithmetic_expression
               | IDENTIFIER DIVIDEASSIGN arithmetic_expression
               | IDENTIFIER DIVIDE_FLOORASSIGN arithmetic_expression
               | IDENTIFIER DIVIDE_CEILASSIGN arithmetic_expression
               | IDENTIFIER GREATER_THANASSIGN arithmetic_expression
               | IDENTIFIER SMALLER_THANASSIGN arithmetic_expression
               | IDENTIFIER GREATER_EQUALSASSIGN arithmetic_expression
               | IDENTIFIER SMALLER_EQUALSASSIGN arithmetic_expression
               | IDENTIFIER EQUALSASSIGN arithmetic_expression
               | IDENTIFIER UNEQUALSASSIGN arithmetic_expression
               | IDENTIFIER ANDASSIGN arithmetic_expression
               | IDENTIFIER ORASSIGN arithmetic_expression
               | IDENTIFIER XORASSIGN arithmetic_expression
               | IDENTIFIER EXPASSIGN arithmetic_expression
               | IDENTIFIER MODASSIGN arithmetic_expression
    """
    p[0] = ("assign", look_up_table2[p[2]], p[1], p[3])


def p_sequence(p):
    """
    sequence : BEGIN statements END
            | BEGIN statements SEMICOLON END
    """
    p[0] = ("seq", p[2])


def p_statements1(p):
    """
    statements : expression
    | arithmetic_expression
    | statement
    | sequence
    """
    p[0] = [p[1]]


def p_statements2(p):
    """statements : statements SEMICOLON expression
    | statements SEMICOLON arithmetic_expression"""
    p[0] = p[1] + [p[3]]


def p_if_statements1(p):
    """
    statement : IF expression THEN statements ENDCOND
               | IF expression THEN statements else_elif_body ENDCOND
    """
    if len(p) == 6:
        p[0] = ("if", p[2], p[4], None)
    else:
        p[0] = ("if", p[2], p[4], p[5])  # elif


def p_if_statements2(p):
    """
    else_elif_body : ELIF IF expression THEN statements else_elif_body
    | ELSE statements
    """
    if len(p) == 3:
        p[0] = p[2]
    else:
        p[0] = [(p[3], p[5])] + p[6]


def p_while_statement(p):
    """
    statement : WHILE expression THEN statements
    """
    p[0] = ("while", p[2], p[4])


def p_loop_statement(p):
    """
    statement : LOOP IDENTIFIER LOOPIN interval LOOPTHEN statements ENDCOND
    """
    p[0] = ("loop", p[2], p[4], p[6])


def p_interval(p):
    """
    interval : '[' expression ',' expression ']'
             | ']' expression ',' expression ']'
             | '[' expression ',' expression '['
             | ']' expression ',' expression '['
    """
    p[0] = (p[1], p[2], p[4], p[5])


def p_error(p):
    if p:
        print(f"Syntaxfehler bei Token '{p.value}' vom Typ {p.type}")
        print_error_with_caret(p.lexer.lexdata, p.lineno, p.lexpos)
    else:
        print("Syntaxfehler: Unerwartetes Dateiende")


precedence = (
    tuple(["right", "ASSIGN"] + [a for a in assigns]),
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

parser = yacc(start="sequence")

if __name__ == "__main__":
    # Eigene Cases
    print("Please start the main File in test/")
    res = parser.parse("{" + input() + "}")
    print(res)
