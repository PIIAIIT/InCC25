from lexer import lexer
from parser import parser
from interpreter import eval
from environment import Environment
from pathlib import Path
from _builtin import BuiltinFunction, builtin_print, builtin_len, builtin_list

start_env = Environment()
builtins = {
    "echo": BuiltinFunction(builtin_print),
    "länge": BuiltinFunction(builtin_len),
    "list": BuiltinFunction(builtin_list),
    "type": BuiltinFunction(lambda pos, _: type(pos[0]))
}

for name, fn in builtins.items():
    start_env[name] = fn


__BASE_DIR = Path(__file__).resolve().parent.parent
__SEARCH_PATH = __BASE_DIR / "test"
__FILE_END = ".ice"
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
        for f in d.glob(f"*{__FILE_END}"):
            content = f.read_text(encoding="utf-8")
            code_files.append((f, content))
            if verbose:
                print(f"\n--- {f} ---\n{content}")

    return code_files  # Liste von (Pfad, Inhalt)


ALL_TEST_FILES = __read_file()


def read_file(incc25_file, verbose=False):
    for posix_file, content in ALL_TEST_FILES:
        if posix_file == incc25_file:
            print(incc25_file, "done.") if verbose else ""
            print(content) if verbose else ""
            return content
    return None


def test_lexer(input_string, verbose=False):
    if input_string is None:
        print("Es ist ein Fehler mit dem InputStream.")
    input_string = input_string.strip("\n")

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

    try:
        res = parser.parse(input_string, debug=verbose)
    except Exception:
        res = False
    return res is not None


def test_interpreter(input_string, env=start_env, verbose=False):
    if input_string is None:
        print("Es ist ein Fehler mit dem InputStream.")

    ast = parser.parse(input_string, debug=verbose)
    print(ast, end=" === ") if verbose else ""
    res = eval(ast, env, verbose)
    print(res) if verbose else ""
    return res


# MEINE SPRACHE SOLL FOLGENDE EIGENSCHAFTEN HABEN #
# ATOMIC
assert test_interpreter("5") == 5
assert test_interpreter("0x5") == 5
assert test_interpreter("0b101") == 5
assert test_interpreter("3.14") == 3.14
# assert not test_parser(".14")
# assert not test_parser("3.")
assert test_interpreter("x", env={"x": 7}) == 7
assert test_interpreter("3 imag") == 3j
assert test_interpreter("(2 + 3) imag") == 5j
assert test_interpreter("2 + 3 imag") == 2+3j
assert test_interpreter("(2 + 3) imag + 1") == 1 + 5j
assert test_interpreter("(2 + 3)e 2") == 500
assert test_interpreter("π", env={"π": 3.1415}) == 3.1415

# BINOPS
assert test_interpreter("2 + 3") == 5
assert test_interpreter("7 - 4") == 3
assert test_interpreter("5 * 6") == 30
assert test_interpreter("8 / 2") == 4.0
assert test_interpreter("9 mod 4") == 1
assert test_interpreter("0 mod 1") == 0
try:
    a = test_interpreter("1 mod 0")
    raise Exception("Kein Zero Division Error!")
except ZeroDivisionError:
    pass

assert test_interpreter("2 ** 3") == 8
assert test_interpreter("0 ** 0") == 1
assert test_interpreter("0 ** 1") == 0

assert test_interpreter("7 | 3") == 7 / 3  # normale Division
assert test_interpreter("-7 / 3") == -2  # Aufrunden Minus
assert test_interpreter("7 / 3") == 3  # Aufrunden
assert test_interpreter("-7 \\ 3") == -3  # Abrunden Minus
assert test_interpreter("7 \\ 3") == 2  # Abrunden

assert test_interpreter("3 = 3") == 1
assert test_interpreter("4 > 2") == 1
assert test_interpreter("2 < 5") == 1
assert test_interpreter("4 = 4 != 5") == 1
assert test_interpreter("4 = 4 != 4") == 0
assert test_interpreter("3 = 3 = 3 = 4") == 0
assert test_interpreter("3 = 3 = 3 = 3") == 1
assert test_interpreter("4 > 2 > -2") == 1
assert test_interpreter("2 < 5 < 2 e 10 > 0") == 1
assert test_interpreter("3 != 4") == 1
assert test_interpreter("4 != 4") == 0
assert test_interpreter("5 <= 5") == 1
assert test_interpreter("6 <= 5") == 0
assert test_interpreter("6 >= 5") == 1
assert test_interpreter("6 >= x", env={"x": 12}) == 0

# COMPS
assert test_interpreter("1 and 1") == 1
assert test_interpreter("0 and x", env={"x": 1}) == 0
assert test_interpreter("1 or x", env={"x": 0}) == 1
assert test_interpreter("1 or 0") == 1
assert test_interpreter("1 xor 0") == 1
assert test_interpreter("1 xor 1") == 0
assert test_interpreter("not 1") == 0
assert test_interpreter("not not 1") == 1
assert test_interpreter("not 0") == 1
assert test_interpreter("not (1 and 0)") == 1

# UNARY
assert test_interpreter("-5") == -5
assert test_interpreter("-(+5)") == -5
assert test_interpreter("+5") == 5
assert test_interpreter("-(+(-(-5)))") == -5
assert test_interpreter("+(-5)") == 5
assert test_interpreter("not -1") == 0

# ENVIRONMENT / ASSIGNMENT
new_env = Environment(start_env)
assert test_interpreter("a := 7", new_env) == 7
assert new_env["a"] == 7
assert test_interpreter("a := (x:=2) + 5", new_env) == 7
assert new_env["x"] == 2
assert new_env["a"] == 7
assert test_interpreter("{a:=2; a+:=3; a}") == 5
assert test_interpreter("{a:=2; a-:=5; a}") == -3
assert test_interpreter("{a:=3; a*:=-2; a}") == -6
assert test_interpreter("{a:=4; a/:=2; a}") == 2

# COMPLEX COMPS/BINOPS/UNARY
assert test_interpreter("(2 + -3) * 4") == -4
assert test_interpreter("{2 < 5 <2 e 10 > 0}") == 1
assert test_interpreter("{2 < 5 and 5<2 e 10 and 2e 10 > 0}") == 1
assert test_interpreter("{(2 < 5) and (5<2 e 10) and (2e 10 > 0)}") == 1
new_env = Environment(new_env)
new_env.put(["x"])
new_env["x"] = 0
assert test_interpreter("{(2 < 5) and (5<2 e 10) and (2e 10 > 5) and (x:=1)}", env=new_env) == 1
assert new_env["x"] == 1
assert test_interpreter("{x:=2<3; x:=x+1; x}", env={"x": 2}) == 2

test_code = r"""
{
a:=1;
b:=2;
a+:=b * 3;
a
}
"""
assert test_interpreter(test_code) == 7

test_code = r"""
{
x:=0;
x:=x+1;
x:=x+1;
x:=x+1;
x
}
"""
assert test_interpreter(test_code) == 3

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
x:=3;
y:=5;
(x<y and y>x) or (x=y)
}
"""
assert test_interpreter(test_code) == 1

test_code = r"""
{
z:=0;
x:=1 or (z:=1);
z
}
"""
assert test_interpreter(test_code) == 1  # short-circuit: z bleibt 0

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

ALL_PATHS = [x for x, _ in ALL_TEST_FILES]
v = False
################### LEXER TEST ###################
for path in ALL_PATHS:
    assert test_lexer(read_file(path), verbose=v)

################### PARSER TEST ###################
for path in ALL_PATHS:
    assert test_parser(read_file(path), verbose=v)

################### INTERPRETER TEST ###################
for path in ALL_PATHS:
    assert test_interpreter(read_file(path), verbose=v)
