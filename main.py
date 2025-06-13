from parser import parser
from environment import Environment
from interpreter import eval
from lexer import lexer
import sys

env = Environment()


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

        try:
            r = eval(result, env)
            print(r)
        except Exception as e:
            print(e)
            print("Fehler bei der Eingabe: ", i)


if __name__ == "__main__":
    debug = False

    for eachArg in sys.argv:
        if eachArg == "-debug":
            debug = True

    env.put(["x", "y", "z"])
    test_code(debug)
