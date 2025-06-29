from parser import parser
from environment import Environment
from interpreter import eval
from lexer import lexer
import readline
import sys

env = Environment()
env.builtins()


def test_code(debug=False):
    while True:
        try:
            i = input(">>> ")
            if i in " \t\n":
                continue
            if i == "q":
                break
            result = parser.parse("{" + i + "}", debug=debug)
            if debug:
                print(result)

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

    test_code(debug)
