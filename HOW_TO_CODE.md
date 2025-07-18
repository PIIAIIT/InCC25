# Sprachspezifikation: Ausdrucksparser

Diese Datei beschreibt die Grammatik der Ausdruckssprache in Erweiterten Backus-Naur Form. Sie wurde aus der `parser.out`-Datei von PLY generiert.

---

## Startsymbol

```
S' ::= <expr>
```



## Ausdrucksregeln
```
`<binop>` ::= PLUS | MINUS | TIMES | DIVIDE | DIVIDE_CEIL | DIVIDE_FLOOR | MOD | EXP | AND | OR | XOR | POWER
`<unary>` ::= NOT | MINUS | PLUS
`<expr>` ::= NUMBER | FLOAT | STRING | IDENTIFIER
          | LPAREN <expr> RPAREN
          | <expr> <binop> <expr>
          | <unary> <expr>
          | <expr> IMAG
```

## Vergleichsoperationen
```
`<comps>` ::= GREATER_THAN | SMALLER_THAN | UNEQUALS | EQUALS | SMALLER_EQUALS | GREATER_EQUALS
`<comparison>`  ::= <expr> <comps> <expr>
                  | <comparison> <comps> <expr>
`<expr>` ::= <comparison>
```


## Zuweisungen
```
`<expr>` ::= IDENTIFIER [<binop> | <comps>] ASSIGN <expr>
```

## Kontrollstrukturen
### IF/ELSE/ELIF
```
`<expr>` ::= IF <expr> THEN COMMA <expr> [<else_body>] DOT

`<else_body>` ::= COMMA ELIF IF <expr> THEN COMMA <expr> [<else_body>]
                | ELSE <expr>
```


### Schleifen
```
`<expr>` ::= WHILE <expr> THEN COMMA <expr> DOT
           | LOOP IDENTIFIER IN <expr> LOOPTHEN <expr> DOT

`<expr>` ::= (OPEN_BRACKETS|CLOSED_BRACKETS) <expr> ITER <expr> (OPEN_BRACKETS|CLOSED_BRACKETS)
```


## Lambda-Ausdrücke
```
`<expr>` ::= LAMBDA <parameter> LAMBDA_ARROW <expr>
          | <expr> LPAREN <parameter_expr> RPAREN

`<parameter>` ::= LPAREN <parameter_pos> RPAREN
              | IDENTIFIER
              | empty

`<parameter_pos>` ::= <parameter_pos_list>
`<parameter_pos_list>` ::= IDENTIFIER [COMMA <parameter_pos_list>]
                       | <parameter_keywords>

`<parameter_keywords>` ::= <parameter_kw_list>
`<parameter_kw_list>` ::= IDENTIFIER COLON <expr> [COMMA <parameter_kw_list>]
                      | <parameter_infty>
`<parameter_infty>` ::= IDENTIFIER DOTS

`<parameter_expr>` ::= <parameter_pos_expr>
                   | empty

`<parameter_pos_expr>` ::= <expr> [COMMA <parameter_pos_expr>]
                       | <parameter_keywords_expr>

`<parameter_keywords_expr>` ::= <expr> COLON <expr> [COMMA <parameter_keywords_expr>]
```

## Blöcke und Sequenzen
```
`<expr>` ::= BEGIN [<statements> [SEMICOLON]] END

`<statements>` ::= <expr>
               | <statements> SEMICOLON <expr>
```

## Listen, Arrays und Strukturen
```
`<param_list>` ::= <expr> COMMA <param_list>
`<param_list>` ::= <expr> COMMA <expr>
`<expr>` ::= <expr> CONS <expr>
          | LPAREN <param_list> RPAREN
          | NULL

`<expr>` ::= <expr> OPEN_BRACKETS (PLUS | <expr> ) CLOSED_BRACKETS
          | OPEN_BRACKETS [<param_list> | <expr>] CLOSED_BRACKETS

`<assignment_list>` ::= <assign_expr> SEMICOLON <assignment_list>
`<assignment_list>` ::= <assign_expr> SEMICOLON <assign_expr>
`<expr>` ::= STRUCT BEGIN [<assignment_list> | <assign_expr>] END

`<expr>` ::= <expr> LAMBDA_ARROW <expr>
```

## Sonstige Konstrukte
```
`<let_assign>` ::= IDENTIFIER EQUALS <expr> [COMMA <let_assign>]
                 | IDENTIFIER EQUALS <expr>

`<expr>` ::= LET <let_assign> IN <expr> DOT
           | MATCH <expr> WITH <cases> DOT
           | IMPORT <file>

`<cases>` ::= CASE <expr> COLON <expr> DOT [<cases>]

`<file>` ::= STRING
```

## Leere Produktionen
```
`<empty>` ::= NULL
```
