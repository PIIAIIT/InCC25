from parser import parser

from interpreter import eval
from lexer import lexer

# code = input("rpl >")
#
# lexer.input(code)
# print("Ausgabe von Lexer:")
# for tok in lexer:
#     print(tok)
#
# print("Ausgabe von Praser:")
# result = parser.parse(code)
# print(result)

env = {"x": 0, "y": 0, "z": 0, "a": 0}


def test_code(code=None):
    print("Ausgabe des Interpreters:")

    if code is not None:
        for line in code.splitlines("\n"):
            result = parser.parse(line)
            # print(result)

            r = eval(result, env)
            print(f"input = {line}, result = {r}")
            # Visualisieren
            # dot = ast_to_graphviz(result)
            # dot.render("ast", view=True)
            # time.sleep(1)

    else:
        while True:
            i = input(">>> ")
            if i == "q":
                break
            i = "{" + i + "}"
            result = parser.parse(i)
            print(result)

            r = eval(result, env)
            print(f"input = {i}, result = {r}")


test_code("{2 < 5 <2 e 10 > 0}")  # Geht noch nicht
test_code("{2 < 5 and 5<2 e 10 and 2e 10 > 0}")
test_code("{x:=2<3; x:=x+1; x}")
test_code()
