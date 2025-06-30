from ply.yacc import yacc
from lexer import tokens, print_traceback, op_assigns
import readline, traceback

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
    "expression : NUMBER"
    p[0] = ("num", p[1])


def p_float(p):
    "expression : FLOAT"
    p[0] = ("float", p[1])


def p_string(p):
    "expression : STRING"
    p[0] = ("str", p[1])


def p_var(p):
    "expression : IDENTIFIER"
    p[0] = ("var", p[1])


def p_paran(p):
    "expression : LPAREN expression RPAREN"
    p[0] = p[2]


################ EXPRESSION ################


def p_arithmetic_expression(p):
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
                  | expression POWER expression
    """
    p[0] = ("binop", look_up_table[p[2]], p[1], p[3])


def p_unary(p):
    """expression : NOT   expression
    | MINUS expression %prec UMINUS
    | PLUS  expression %prec UPLUS"""
    p[0] = ("unary", unary[p[1]], p[2])


def p_complex(p):
    """expression : expression IMAG"""
    p[0] = ("complex", p[1])


################ COMPARISON EXPRESSION ################


def p_expression_comparison_chain1(p):
    """
    comparison : expression comparison_op expression %prec CMP
    """
    p[0] = [p[2], p[1], p[3]]


def p_expression_comparison_chain2(p):
    """
    comparison : comparison comparison_op expression %prec CMP2
    """
    p[0] = [p[1][0] + [p[2]], p[1][1] + [p[3]]]


def p_expression1(p):
    """expression : comparison %prec CLS"""
    p[0] = ("comparison", *p[1])


def p_comparison_op(p):
    """comparison_op : GREATER_THAN
    | SMALLER_THAN
    | UNEQUALS
    | EQUALS
    | SMALLER_EQUALS
    | GREATER_EQUALS"""
    p[0] = look_up_table[p[1]]


################ ASSIGNMENTS ################


def p_assignment1(p):
    "assign_expression : IDENTIFIER ASSIGN expression %prec ASSIGN"
    p[0] = ("assign", None, p[1], p[3])


def p_assignment3(p):
    "expression : assign_expression"
    p[0] = p[1]


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
################ STATEMENTS ################

def p_sequence(p):
    """
    expression : BEGIN statements END
               | BEGIN statements SEMICOLON END
               | BEGIN END
    """
    if len(p) == 3:
        p[2] = []
    p[0] = ("seq", p[2])


def p_statement(p):
    """
    statements : expression
    """
    p[0] = [p[1]]


def p_statements(p):
    """
    statements : statements SEMICOLON expression
    """
    p[0] = p[1] + [p[3]]


######################### IF #########################


def p_if_statements1(p):
    """
    expression : IF expression THEN COMMA expression DOT
               | IF expression THEN COMMA expression else_elif_body DOT
    """
    if len(p) == 7:
        p[0] = ("if", p[2], p[5], None)
    else:
        p[0] = ("if", p[2], p[5], p[6])  # elif


def p_if_statements2(p):
    """
    else_elif_body : COMMA ELIF IF expression THEN COMMA expression else_elif_body
                   | ELSE expression
    """
    if len(p) == 3:
        p[0] = [("else", p[2])]
    else:
        p[0] = [(p[4], p[7]), *p[8]]


######################### WHILE #########################


def p_while_statement0(p):
    """
    expression : WHILE expression THEN COMMA expression DOT
    """
    p[0] = ("while", p[2], p[5])


######################### LOOP #########################


def p_loop_statement0(p):
    """
    expression : LOOP IDENTIFIER IN expression LOOPTHEN expression DOT
    """
    p[0] = ("loop", p[2], p[4], p[6])


def p_interval(p):
    """
    expression : OPEN_BRACKETS   expression ITER expression CLOSED_BRACKETS
               | CLOSED_BRACKETS expression ITER expression CLOSED_BRACKETS
               | OPEN_BRACKETS   expression ITER expression OPEN_BRACKETS
               | CLOSED_BRACKETS expression ITER expression OPEN_BRACKETS
    """
    p[0] = ("interval", p[1], p[2], p[4], p[5])


######################### LAMBDA #########################


def p_lambda0(p):
    "expression : LAMBDA parameter LAMBDA_ARROW expression DOT"
    p[0] = ("lambda", p[2], p[4])


def p_parameter0(p):
    """
    parameter : LPAREN parameter_pos RPAREN
              | IDENTIFIER
              | empty
    """
    if len(p) == 4:
        p[0] = ("parameter", p[2])
    elif isinstance(p[1], list):
        p[0] = ("parameter", p[1])
    else:
        p[0] = ("parameter", [("pos", p[1])])


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
        p[0] = [("pos", p[1]), *p[3]]
    elif isinstance(p[1], list):
        p[0] = p[1]
    else:
        p[0] = [("pos", p[1])]


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
        p[0] = [("pos", p[1]), *p[3]]
    elif isinstance(p[1], tuple):
        p[0] = [("pos", p[1])]
    else:
        p[0] = p[1]


def p_parameter8(p):
    """
    parameter_keywords_expr : expression COLON expression COMMA parameter_keywords_expr
                            | expression COLON expression
    """
    if len(p) == 6:
        p[0] = [("keyword", p[1], p[3]), *p[5]]
    elif len(p) == 4:
        p[0] = [("keyword", p[1], p[3])]


def p_empty(p):
    "empty :"
    p[0] = []


def p_call(p):
    """expression : expression LPAREN parameter_expr RPAREN"""
    p[0] = ("call", p[1], p[3])


######################### LET #########################
############## Ist Standardmäßig das LETREC ##############

def p_let_assign0(p):
    "let_assign : IDENTIFIER EQUALS expression COMMA let_assign"
    p[0] = [("assign", None, p[1], p[3]), *p[5]]


def p_let_assign1(p):
    "let_assign : IDENTIFIER EQUALS expression"
    p[0] = [("assign", None, p[1], p[3])]


def p_let(p):
    "expression : LET let_assign IN expression DOT"
    p[0] = ("let", p[2], p[4])


######################### LISTS #########################
###################### WIE IN LISP mit KOMMA ######################


def p_paramlist1(p):
    """param_list : expression COMMA param_list
                  | expression COMMA param_list_end
    """
    p[0] = [p[1], *p[3]]


def p_paramlist2(p):
    "param_list_end : expression"
    p[0] = [p[1]]


def p_cons(p):
    "expression : expression CONS expression"
    p[0] = ("cons", p[1], p[3])


def p_list(p):
    "expression : LPAREN param_list RPAREN"
    p[0] = ("list", p[2])


def p_list_zugriff(p):
    """expression : expression OPEN_BRACKETS PLUS       CLOSED_BRACKETS
                  | expression OPEN_BRACKETS expression CLOSED_BRACKETS
    """
    p[0] = ("array_access", p[1], p[3])


def p_leere_liste(p):
    "expression : NULL"
    p[0] = ("leere")


######################### ARRAY #########################


def p_array0(p):
    """expression : OPEN_BRACKETS param_list CLOSED_BRACKETS
    """
    p[0] = ("array", p[2])


def p_array1(p):
    """expression : OPEN_BRACKETS expression CLOSED_BRACKETS
    """
    p[0] = ("array", [p[2]])


def p_array2(p):
    """expression : OPEN_BRACKETS CLOSED_BRACKETS
    """
    p[0] = ("array", [])


######################### STRUCTS #########################

def p_assignment_list0(p):
    """assignment_list : assign_expression COMMA assignment_list
                       | assign_expression COMMA assignment_list_end
    """
    p[0] = [p[1], *p[3]]


def p_assignment_list2(p):
    "assignment_list_end : assign_expression"
    p[0] = [p[1]]


def p_struct0(p):
    "expression : STRUCT BEGIN assignment_list END"
    # struct { assignments, ... }
    # Person := struct { name := "Patrick", alter := 25 }
    p[0] = ("struct", p[3])


def p_struct1(p):
    "expression : STRUCT BEGIN assign_expression END"
    # struct { assignments }
    # Person := struct { name := "Patrick" }
    p[0] = ("struct", [p[3]])


def p_struct2(p):
    "expression : STRUCT BEGIN END"
    # struct { }
    # Person := struct { }
    p[0] = ("struct", [])


def p_access_structs(p):
    "expression : expression LAMBDA_ARROW expression"
    # Person->name
    # Person->alter
    p[0] = ("access_struct", p[1], p[3])


######################### IMPORT #########################

def p_file(p):
    "file : STRING"
    p[0] = [p[1][1:-1]]


def p_import(p):
    "expression : IMPORT file"
    p[0] = ("import", p[2])

######################### MATCH #########################


def p_match(p):
    "expression : MATCH expression WITH cases DOT"
    p[0] = ("match", p[2], p[4])


def p_cases0(p):
    "cases : CASE expression COLON expression DOT cases"
    p[0] = [(p[2], p[4]), *p[6]]


def p_cases1(p):
    "cases : CASE expression COLON expression DOT"
    p[0] = [(p[2], p[4])]


######################### TRACEBACK ##############################


def p_error(p):
    if p:
        print_traceback(p.lexer.lexdata, p)
        print(f"Syntaxfehler bei Token '{p.value}' vom Typ {p.type}")
    else:
        print("Syntaxfehler: Unerwartetes Dateiende")


########################################################

precedence = (
    ("right", "ASSIGN"),
    ("right", *(a for a in op_assigns.values())),
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
    ("left", "LAMBDA_ARROW"),
    ("left", "OPEN_BRACKETS", "CLOSED_BRACKETS", "LPAREN", "RPAREN", "BEGIN", "END"),
)

########################################################

parser = yacc(start="expression")

if __name__ == "__main__":
    # Interaktives Menu
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
