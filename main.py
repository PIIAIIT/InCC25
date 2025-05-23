from parser import parser
from environment import Environment
from interpreter import eval
from lexer import lexer

env = Environment()
env.put(["x", "y", "z"])


def test_code(debug=False):
    while True:
        i = input(">>> ")
        if i in " \t\n":
            continue
        if i == "q":
            break
        i = "{" + i + "}"
        # try:
        result = parser.parse(i, debug=debug)
        if debug:
            print(result)

        r = eval(result, env)
        print(r)
        # except Exception:
        #     print("Fehler bei der Eingabe: ", i)


test_code()
