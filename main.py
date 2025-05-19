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


def test_code(debug=False):
    while True:
        i = input(">>> ")
        if i in " \t\n":
            continue
        if i == "q":
            break
        i = "{" + i + "}"
        try:
            result = parser.parse(i, debug=debug)
            if debug:
                print(result)

            r = eval(result, env)
            # print(f"input = {i}, result = {r}")
            print(r)
        except Exception:
            print("Fehler bei der Eingabe: ", i)


test_code()
