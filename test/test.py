from interpreter import eval
from parser import parser
import os

env = {"x": 0}

verbose = False

path = os.path.abspath(".") + "/test/"
print(path)


def read_file(incc25_file):
    with open(path + incc25_file, "r+") as f:
        code = f.read()
    return code


print(read_file("test1.incc25"))


def parse_and_eval(input_string, env=None, verbose=False):
    input_string = input_string.strip("\n")
    if not input_string.startswith("{") or not input_string.endswith("}"):
        input_string = "{\n" + input_string + "\n}"

    if env is None:
        env = {}
    ast = parser.parse(input_string)
    print(ast, end=" === ") if verbose else ""
    res = eval(ast, env)
    print(res) if verbose else ""
    return res


assert parse_and_eval("5") == 5
assert parse_and_eval("3.14") == 3.14
assert parse_and_eval("x", env={"x": 7}) == 7

assert parse_and_eval("2 + 3") == 5
assert parse_and_eval("7 - 4") == 3
assert parse_and_eval("5 * 6") == 30
assert parse_and_eval("8 / 2") == 4.0
assert parse_and_eval("9 mod 4") == 1
assert parse_and_eval("2 ** 3") == 8

assert parse_and_eval("7 | 3") == 7 / 3  # normale Division
assert parse_and_eval("7 / 3") == 3  # Aufrunden
assert parse_and_eval(r"7 \ 3") == 2  # Abrunden

assert parse_and_eval("3 = 3") == 1
assert parse_and_eval("4 > 2") == 1
assert parse_and_eval("2 < 5") == 1
assert parse_and_eval("3 = 3 = 3 = 4") == 0
assert parse_and_eval("3 = 3 = 3 = 3") == 1
assert parse_and_eval("4 > 2 > -2") == 1
assert parse_and_eval("2 < 5 < 2 e 10 > 0") == 1
assert parse_and_eval("3 != 4") == 1
assert parse_and_eval("5 <= 5") == 1
assert parse_and_eval("6 >= 5") == 1

assert parse_and_eval("1 and 1") == 1
assert parse_and_eval("1 or 0") == 1
assert parse_and_eval("1 xor 0") == 1
assert parse_and_eval("1 xor 1") == 0
assert parse_and_eval("not 1") == 0
assert parse_and_eval("not 0") == 1

assert parse_and_eval("-5") == -5
assert parse_and_eval("+5") == 5
assert parse_and_eval("+(-5)") == 5

env = {}
assert parse_and_eval("a := 7", env) == 7
assert env["a"] == 7

assert parse_and_eval("(2 + 3) * 4") == 20

assert parse_and_eval("3 imag") == 3j
assert parse_and_eval("(2 + 3) imag") == 5j


test_code = r"""
{
x:= 3;
x:=0+3*5-(-3);
x + 3;
x:= x + 3
}
"""

assert parse_and_eval(test_code) == 21

test_code = r"""
{
x:= 21;
x:= -x**3;
x:=-x-2;
x mod 5;
}
"""
# 2. 7999
assert parse_and_eval(test_code) == 2


test_code = r"""
{
x:= 21;
x:= -x**3;
x:=-x-2;
x mod 5;
y:=0xff + 0b11 + -x - 5 e 10;
}
"""
# 2. 7999
assert parse_and_eval(test_code) == -50000009005

test_code = r"""
{
x:=-49999999742;
x := 256;
x := x mod 5 \ 4 - 10 ** (4 | 2 + 3) / 5;
i_me:=420.69
}"""

assert parse_and_eval(test_code) == 420.69
################### FILE TEST ###################

loesung = parse_and_eval("1+2+3+4+5+3+7+8+3+5")
assert parse_and_eval(read_file("test1.incc25")) == loesung

# assert parse_and_eval(read_file("test2.incc25")) ==
