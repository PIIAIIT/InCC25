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
look_up_assignments = {}
for k, v in look_up_table.items():
    look_up_assignments[k + ":="] = v
unary = {
    "not": "not",
    "-": "uminus",
    "+": "uplus",
}

################ ATOMIC ################


def p_number(p):
    "atomar : NUMBER"
    p[0] = ("num", p[1])


def p_float(p):
    "atomar : FLOAT"
    p[0] = ("float", p[1])


def p_string(p):
    "atomar : STRING"
    p[0] = ("str", p[1])


def p_var(p):
    "atomar : IDENTIFIER"
    p[0] = ("var", p[1])


def p_paran(p):
    "atomar : LPAREN expression RPAREN"
    p[0] = p[2]


################ EXPRESSION ################


def p_expression0(p):
    """expression : arithmetic_expression"""
    p[0] = p[1]


################ ARITHMETIC EXPRESSION ################


def p_arithmetic_expression(p):
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
    """
    p[0] = ("binop", look_up_table[p[2]], p[1], p[3])


def p_unary(p):
    """arithmetic_expression : NOT   arithmetic_expression
    | MINUS arithmetic_expression %prec UMINUS
    | PLUS  arithmetic_expression %prec UPLUS"""
    p[0] = ("unary", unary[p[1]], p[2])


def p_complex(p):
    """arithmetic_expression : arithmetic_expression IMAG"""
    p[0] = ("complex", p[1])


def p_arithmetic_end(p):
    """arithmetic_expression : atomar"""
    p[0] = p[1]


################ COMPARISON EXPRESSION ################


def p_expression_comparison_chain1(p):
    """
    comparison : arithmetic_expression comparison_op arithmetic_expression comparison_chain
    """
    p[0] = ("comparison_chain", p[1], [(p[2], p[3])] + p[4])


def p_expression_comparison_chain2(p):
    """
    comparison : arithmetic_expression comparison_op arithmetic_expression
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


def p_expression1(p):
    """expression : comparison"""
    p[0] = p[1]


################ ASSIGNMENTS ################


def p_assignment1(p):
    "expression : IDENTIFIER ASSIGN expression %prec ASSIGN"
    p[0] = ("assign", None, p[1], p[3])


def p_assignment2(p):
    """
    expression : IDENTIFIER PLUS_ASSIGN expression
               | IDENTIFIER MINUS_ASSIGN expression
               | IDENTIFIER TIMES_ASSIGN expression
               | IDENTIFIER POWER_ASSIGN expression
               | IDENTIFIER DIVIDE_ASSIGN expression
               | IDENTIFIER DIVIDE_FLOOR_ASSIGN expression
               | IDENTIFIER DIVIDE_CEIL_ASSIGN expression
               | IDENTIFIER GREATER_THAN_ASSIGN expression
               | IDENTIFIER SMALLER_THAN_ASSIGN expression
               | IDENTIFIER GREATER_EQUALS_ASSIGN expression
               | IDENTIFIER SMALLER_EQUALS_ASSIGN expression
               | IDENTIFIER EQUALS_ASSIGN expression
               | IDENTIFIER UNEQUALS_ASSIGN expression
               | IDENTIFIER AND_ASSIGN expression
               | IDENTIFIER OR_ASSIGN expression
               | IDENTIFIER XOR_ASSIGN expression
               | IDENTIFIER EXP_ASSIGN expression
               | IDENTIFIER MOD_ASSIGN expression
    """
    p[0] = ("assign", look_up_assignments[p[2]], p[1], p[3])


################ SEQUENCE ################


def p_sequence(p):
    """
    sequence : BEGIN statements END
             | BEGIN statements SEMICOLON END
    """
    p[0] = ("seq", p[2])


def p_expression2(p):
    """expression : sequence"""
    p[0] = p[1]


################ STATEMENTS ################


def p_statement0(p):
    """
    statement : expression
              | if_statement
              | while_statement
              | loop_statement
    """
    p[0] = p[1]


def p_statements0(p):
    """
    statements : statements SEMICOLON statement
    """
    p[0] = p[1] + [p[3]]


def p_statements1(p):
    """
    statements : statement
    """
    p[0] = [p[1]]


######################### IF #########################


def p_if_statements1(p):
    """
    if_statement : IF expression THEN statements DOT
                 | IF expression THEN statements else_elif_body DOT
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
        p[0] = [("None", p[2])]
    else:
        p[0] = [(p[3], p[5]), *p[6]]


######################### WHILE #########################


def p_while_statement(p):
    """
    while_statement : WHILE expression THEN statements DOT
    """
    p[0] = ("while", p[2], p[4])


######################### LOOP #########################


def p_loop_statement(p):
    """
    loop_statement : LOOP IDENTIFIER IN interval LOOPTHEN statements DOT
    """
    p[0] = ("loop", p[2], p[4], p[6])


def p_interval(p):
    """
    interval : OPEN_BRACKETS   expression COMMA expression CLOSED_BRACKETS
             | CLOSED_BRACKETS expression COMMA expression CLOSED_BRACKETS
             | OPEN_BRACKETS   expression COMMA expression OPEN_BRACKETS
             | CLOSED_BRACKETS expression COMMA expression OPEN_BRACKETS
    """
    p[0] = (p[1], p[2], p[4], p[5])


######################### LAMBDA #########################


def p_lambda0(p):
    "lambda : LAMBDA parameter LAMBDA_ARROW expression"
    p[0] = ("lambda", p[2], p[4])


def p_lambda1(p):
    "expression : lambda"
    p[0] = p[1]


def p_parameter0(p):
    """
    parameter : LPAREN parameter_pos RPAREN
              | IDENTIFIER
              | empty
    """
    if len(p) == 4:
        p[0] = ("parameter", p[2])
    else:
        p[0] = ("parameter", p[1])


def p_parameter1(p):
    """
    parameter_pos : parameter_pos_list
    """
    p[0] = p[1]


def p_parameter2(p):
    """
    parameter_pos_list : IDENTIFIER COMMA parameter_pos_list
                       | IDENTIFIER
                       | parameter_keywords
    """
    if len(p) == 4:
        p[0] = [p[1], *p[3]]
    elif isinstance(p[1], list):
        p[0] = [*p[1]]
    else:
        p[0] = [p[1]]


def p_parameter3(p):
    """
    parameter_keywords : parameter_kw_list
    """
    p[0] = p[1]


def p_parameter4(p):
    """
    parameter_kw_list : IDENTIFIER COLON expression COMMA parameter_kw_list
                      | IDENTIFIER COLON expression
                      | parameter_infty
    """
    if len(p) == 6:
        p[0] = [("keyword", p[1], p[3]), *p[5]]
    elif len(p) == 4:
        p[0] = [("keyword", p[1], p[3])]
    else:
        p[0] = p[1]


def p_parameter5(p):
    """
    parameter_infty : IDENTIFIER DOTS
    """
    p[0] = [("infty", p[1])]


def p_parameter6(p):
    """
    parameter_expr : parameter_pos_expr
                   | empty
    """
    p[0] = ("parameter_expr", p[1])


def p_parameter7(p):
    """
    parameter_pos_expr : expression COMMA parameter_pos_expr
                       | expression
                       | parameter_keywords_expr
    """
    if len(p) == 4:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]


def p_parameter8(p):
    """
    parameter_keywords_expr : expression COLON expression COMMA parameter_keywords_expr
                            | expression COLON expression
    """
    if len(p) == 6:
        p[0] = [("keyword", p[1], p[3])] + p[5]
    elif len(p) == 4:
        p[0] = [("keyword", p[1], p[3])]


def p_empty(p):
    "empty :"
    p[0] = []


def p_call(p):
    "expression : atomar LPAREN parameter_expr RPAREN"
    p[0] = ("call", p[1], p[3])


######################### LET #########################
############## Ist Standardmäßig das LETREC ##############


def p_let(p):
    "expression : LET IDENTIFIER EQUALS expression IN expression DOT"
    p[0] = ("let", ("assign", None, p[2], p[4]), p[6])


######################### BUILTIN #########################


def p_builtin_func(p):
    """
    expression : ECHO   LPAREN param_list RPAREN
               | LENGTH LPAREN param_list RPAREN
               | LIST   LPAREN param_list RPAREN
    """
    p[0] = ("function", p[1], p[3])


def p_paramlist1(p):
    "param_list : expression COMMA param_list"
    p[0] = [p[1], *p[3]]


def p_paramlist2(p):
    "param_list : expression"
    p[0] = [p[1]]


######################### LISTS #########################


def p_list_param0(p):
    "list_parameter : expression list_parameter"
    p[0] = [p[1], *p[2]]


def p_list_param1(p):
    "list_parameter : expression"
    p[0] = [p[1]]


def p_list_param2(p):
    "expression : list_parameter"
    p[0] = ("list", p[1])


######################### ARRAY #########################


def p_array(p):
    """expression : OPEN_BRACKETS param_list CLOSED_BRACKETS
    | OPEN_BRACKETS empty      CLOSED_BRACKETS
    """
    p[0] = ("array", p[1])


######################### STRUCTS #########################

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
    ("right", "LPAREN"),  # , "RPAREN"),
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
