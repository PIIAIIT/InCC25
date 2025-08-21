import sys
from parser import parser

from environment import Environment
from interpreter import eval
from lexer import print_traceback

env = Environment()
env.builtins()


ansii = {
    "r": "\001\033[31m\002",
    "g": "\001\033[32m\002",
    "b": "\001\033[34m\002",
    "_": "\001\033[0m\002",
}


def test_code(debug=False):
    while True:
        try:
            src = input(ansii["g"] + ">>> " + ansii["_"])
            multiline = src.strip().endswith("->") or src.count("{") > src.count("}")
            while multiline:
                tmp = input(ansii["g"] + "... " + ansii["_"])
                src += "\n" + tmp  # Zeilen umbrechen
                # Update multiline-Status
                multiline = src.strip().endswith("->") or src.count("{") > src.count(
                    "}"
                )

            result = parser.parse(src, debug=debug)
            if debug:
                print(result)

            print(ansii["b"] + str(eval(result, env)) + ansii["_"])
            # print(r)
        except EOFError:
            exit()
        except Exception as e:
            print(
                ansii["r"]
                + str(print_traceback(src, result, silent=True) if debug else e)
                + ansii["_"]
            )
        except KeyboardInterrupt as e:
            print(e)


if __name__ == "__main__":
    debug = False

    for eachArg in sys.argv:
        if eachArg == "-debug":
            debug = True

    test_code(debug)
