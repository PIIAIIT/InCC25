from lexer import lexer
from parser import parser
from interpreter import eval
from environment import Environment
import math
import os
import sys
from pathlib import Path

env = Environment()
env.put(["x"])

__BASE_DIR = Path(__file__).resolve().parent.parent
__SEARCH_PATH = __BASE_DIR / "test"
ALL_TEST_FILES = []


def __read_file(verbose=False):
    base_path = Path(__SEARCH_PATH).resolve()
    code_files = []

    # Alle Verzeichnisse + das Basisverzeichnis selbst
    ignore_dirs = {"__pycache__"}
    dirs = [base_path] + [
        p for p in base_path.iterdir() if p.is_dir() and p.name not in ignore_dirs
    ]

    for d in dirs:
        for f in d.glob("*.incc25"):
            content = f.read_text(encoding="utf-8")
            code_files.append((f, content))
            if verbose:
                print(f"\n--- {f} ---\n{content}")

    return code_files  # Liste von (Pfad, Inhalt)


ALL_TEST_FILES = __read_file()


def read_file(incc25_file, verbose=False):
    for posix_file, content in ALL_TEST_FILES:
        if str(posix_file).endswith(incc25_file):
            print(content) if verbose else ""
            return content
    return None


def test_lexer(input_string, verbose=False):
    if input_string is None:
        print("Es ist ein Fehler mit dem InputStream.")
    input_string = input_string.strip("\n")
    if not input_string.startswith("{") or not input_string.endswith("}"):
        input_string = "{\n" + input_string + "\n}"

    lexer.input(input_string)
    result = True
    for token in lexer:
        result = result and not str(token).startswith("LexToken(error")

        if verbose:
            print("Korrekte Assersion: " + str(token))
    return result


def test_parser(input_string, verbose=False):
    if input_string is None:
        print("Es ist ein Fehler mit dem InputStream.")
    input_string = input_string.strip("\n")
    if not input_string.startswith("{") or not input_string.endswith("}"):
        input_string = "{\n" + input_string + "\n}"

    res = parser.parse(input_string, debug=verbose)
    return res is not None


def test_interpreter(input_string, env=None, verbose=False):
    if input_string is None:
        print("Es ist ein Fehler mit dem InputStream.")
    input_string = input_string.strip("\n")
    if not input_string.startswith("{") or not input_string.endswith("}"):
        input_string = "{\n" + input_string + "\n}"

    if env is None:
        env = Environment()

    ast = parser.parse(input_string, debug=verbose)
    print(ast, end=" === ") if verbose else ""
    res = eval(ast, env)
    print(res) if verbose else ""
    return res


assert test_interpreter("5") == 5
assert test_interpreter("3.14") == 3.14
assert test_interpreter("x", env={"x": 7}) == 7

assert test_interpreter("2 + 3") == 5
assert test_interpreter("7 - 4") == 3
assert test_interpreter("5 * 6") == 30
assert test_interpreter("8 / 2") == 4.0
assert test_interpreter("9 mod 4") == 1
assert test_interpreter("2 ** 3") == 8

assert test_interpreter("7 | 3") == 7 / 3  # normale Division
assert test_interpreter("7 / 3") == 3  # Aufrunden
assert test_interpreter(r"7 \ 3") == 2  # Abrunden

assert test_interpreter("3 = 3") == 1
assert test_interpreter("4 > 2") == 1
assert test_interpreter("2 < 5") == 1
assert test_interpreter("3 = 3 = 3 = 4") == 0
assert test_interpreter("3 = 3 = 3 = 3") == 1
assert test_interpreter("4 > 2 > -2") == 1
assert test_interpreter("2 < 5 < 2 e 10 > 0") == 1
assert test_interpreter("3 != 4") == 1
assert test_interpreter("4 != 4") == 0
assert test_interpreter("5 <= 5") == 1
assert test_interpreter("6 <= 5") == 0
assert test_interpreter("6 >= 5") == 1

assert test_interpreter("1 and 1") == 1
assert test_interpreter("1 or 0") == 1
assert test_interpreter("1 xor 0") == 1
assert test_interpreter("1 xor 1") == 0
assert test_interpreter("not 1") == 0
assert test_interpreter("not 0") == 1

assert test_interpreter("-5") == -5
assert test_interpreter("+5") == 5
assert test_interpreter("+(-5)") == 5

env = {}
assert test_interpreter("a := 7", env) == 7
assert env["a"] == 7
assert test_interpreter("a := (x:=2) + 5", env) == 7
assert env["x"] == 2
assert env["a"] == 7

assert test_interpreter("(2 + 3) * 4") == 20

assert test_interpreter("3 imag") == 3j
assert test_interpreter("(2 + 3) imag") == 5j

assert test_interpreter("{2 < 5 <2 e 10 > 0}") == 1
assert test_interpreter("{2 < 5 and 5<2 e 10 and 2e 10 > 0}") == 0
assert test_interpreter("{(2 < 5) and (5<2 e 10) and (2e 10 > 0)}") == 1
assert test_interpreter("{x:=2<3; x:=x+1; x}") == 2


test_code = r"""
{
x:=0+3*5-(-3);
x+:=3;
x
}
"""

assert test_interpreter(test_code) == 21

test_code = r"""
{
x:= 21;
x:= -x**3;
x:=-x-2;
x mod 5;
}
"""
assert test_interpreter(test_code) == 4


test_code = r"""
{
x:= 21;
x:= -x**3;
x:=-x-2;
x mod 5;
y:=0xff + 0b11 + -x - 5 e 10;
}
"""
assert test_interpreter(test_code) == -50000009001

test_code = r"""
{
x:=-49999999742;
x := 256;
x := x mod 5 \ 4 - 10 ** (4 | 2 + 3) / 5;
i_me:=420.69
}"""
assert test_interpreter(test_code) == 420.69

################### LEXER TEST ###################
v = False
assert test_lexer(read_file("test1.incc25"), verbose=v)
assert test_lexer(read_file("test2.incc25"), verbose=v)
assert test_lexer(read_file("test3.incc25"), verbose=v)
assert test_lexer(read_file("test6.incc25"), verbose=v)

################### PARSER TEST ###################
assert test_parser(read_file("test1.incc25"), verbose=v)
assert test_parser(read_file("test2.incc25"), verbose=v)
assert test_parser(read_file("test3.incc25"), verbose=v)
assert test_parser(read_file("test6.incc25"), verbose=v)

################### INTERPRETER TEST ###################
assert test_interpreter(read_file("test1.incc25"), verbose=v) == 23
assert test_interpreter(read_file("test2.incc25"), verbose=v) == 2432902008176640000
assert test_interpreter(read_file("test3.incc25"), verbose=v) == 50 / 4
assert test_interpreter(read_file("test4.incc25"), verbose=v) == 17
assert test_interpreter(read_file("test5.incc25"), verbose=v)
assert test_interpreter(read_file("test6.incc25"), verbose=v) == 324
