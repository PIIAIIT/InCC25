# Sprachspezifikation: Ausdrucksparser

Diese Datei beschreibt die Grammatik der Ausdruckssprache in BNF-Notation. Sie wurde aus der `parser.out`-Datei von PLY generiert.

---

## Startsymbol

```bnf
S' ::= expression
```



## Ausdrucksregeln
```bnf
```bnf
`expression` ::= NUMBER
               | FLOAT
               | STRING
               | IDENTIFIER
               | LPAREN expression RPAREN
               | expression PLUS expression
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
               | NOT expression
               | MINUS expression
               | PLUS expression
               | expression IMAG
```

## Vergleichsoperationen
```bnf
`comparison` ::= expression comparison_op expression
               | comparison comparison_op expression

`comparison_op` ::= GREATER_THAN
                  | SMALLER_THAN
                  | UNEQUALS
                  | EQUALS
                  | SMALLER_EQUALS
                  | GREATER_EQUALS

`expression` ::= comparison
```


## Zuweisungen
```bnf
`assign_expression` ::= IDENTIFIER ASSIGN expression

`expression` ::= assign_expression
               | IDENTIFIER PLUS_ASSIGN expression
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
```

## Kontrollstrukturen

### IF/ELSE/ELIF
```bnf
`expression` ::= IF expression THEN COMMA expression DOT
               | IF expression THEN COMMA expression else_elif_body DOT

`else_elif_body` ::= COMMA ELIF IF expression THEN COMMA expression else_elif_body
                   | ELSE expression
                   | COMMA ELIF IF expression THEN COMMA expression
```


### Schleifen
```bnf
`expression` ::= WHILE expression THEN COMMA expression DOT
               | LOOP IDENTIFIER IN expression LOOPTHEN expression DOT

`expression` ::= OPEN_BRACKETS expression ITER expression CLOSED_BRACKETS
               | CLOSED_BRACKETS expression ITER expression CLOSED_BRACKETS
               | OPEN_BRACKETS expression ITER expression OPEN_BRACKETS
               | CLOSED_BRACKETS expression ITER expression OPEN_BRACKETS
```


## Lambda-Ausdrücke
```bnf
`expression` ::= LAMBDA parameter LAMBDA_ARROW expression
               | expression LPAREN parameter_expr RPAREN

`parameter` ::= LPAREN parameter_pos RPAREN
              | IDENTIFIER
              | empty

`parameter_pos` ::= parameter_pos_list
`parameter_pos_list` ::= IDENTIFIER COMMA parameter_pos_list
                       | IDENTIFIER
                       | parameter_keywords

`parameter_keywords` ::= parameter_kw_list
`parameter_kw_list` ::= IDENTIFIER COLON expression COMMA parameter_kw_list
                      | IDENTIFIER COLON expression
                      | parameter_infty

`parameter_infty` ::= IDENTIFIER DOTS
`parameter_expr` ::= parameter_pos_expr
                   | empty

`parameter_pos_expr` ::= expression COMMA parameter_pos_expr
                       | expression
                       | parameter_keywords_expr

`parameter_keywords_expr` ::= expression COLON expression COMMA parameter_keywords_expr
                            | expression COLON expression
```

## Blöcke und Sequenzen
```bnf
`expression` ::= BEGIN statements END
               | BEGIN statements SEMICOLON END
               | BEGIN END

`statements` ::= expression
               | statements SEMICOLON expression
```

## Listen, Arrays und Strukturen
```bnf
`param_list` ::= expression COMMA param_list
`param_list` ::= expression COMMA expression
`expression` ::= expression CONS expression
               | LPAREN param_list RPAREN
               | NULL

`expression` ::= expression OPEN_BRACKETS PLUS CLOSED_BRACKETS
               | expression OPEN_BRACKETS expression CLOSED_BRACKETS
               | OPEN_BRACKETS param_list CLOSED_BRACKETS
               | OPEN_BRACKETS expression CLOSED_BRACKETS
               | OPEN_BRACKETS CLOSED_BRACKETS

`assignment_list` ::= assign_expression SEMICOLON assignment_list
`assignment_list` ::= assign_expression SEMICOLON assign_expression
`expression` ::= STRUCT BEGIN assignment_list END
               | STRUCT BEGIN assign_expression END
               | STRUCT BEGIN END

`expression` ::= expression LAMBDA_ARROW expression
```

## Sonstige Konstrukte
```bnf
`let_assign` ::= IDENTIFIER EQUALS expression COMMA let_assign
               | IDENTIFIER EQUALS expression

`expression` ::= LET let_assign IN expression DOT
               | MATCH expression WITH cases DOT
               | IMPORT file

`cases` ::= CASE expression COLON expression DOT cases
          | CASE expression COLON expression DOT

`file` ::= STRING
```

## Leere Produktionen
```bnf
`empty` ::= <empty>
```


# Anmerkungen
- `LPAREN` = `(`
- `RPAREN` = `)`
- `ASSIGN` = `:=`
- `DOTS` = `...`
- `ITER` = `..`
- `DOT` = `.`
