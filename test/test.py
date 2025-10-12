from lexer import lexer
from parser import parser
from interpreter import eval
from environment import SymbolTable
from pathlib import Path

DEBUG = False


class IceFileManager:
    def __init__(self, base_dir=None, file_suffix=".ice", ignore_dirs=None):
        self.base_dir = Path(base_dir or Path(__file__).resolve().parent.parent)
        self.search_path = self.base_dir / "test"
        self.file_suffix = file_suffix
        self.ignore_dirs = ignore_dirs or {"__pycache__"}

    def _get_dirs(self):
        return [self.search_path] + [
            p
            for p in self.search_path.iterdir()
            if p.is_dir() and p.name not in self.ignore_dirs
        ]

    def find_files(self):
        """Generator für (Pfad, Inhalt)-Tupel"""
        for directory in self._get_dirs():
            for file in directory.glob(f"*{self.file_suffix}"):
                yield file, file.read_text(encoding="utf-8")

    def read_all_files(self, verbose=False):
        """Liest alle Dateien als Liste von (Pfad, Inhalt)"""
        files = []
        for file, content in self.find_files():
            files.append((file, content))
            if verbose:
                print(f"\n--- {file} ---\n{content}")
        return files

    def read_file_by_path(self, filepath, verbose=False):
        for file, content in self.find_files():
            if file == filepath:
                if verbose:
                    print(f"{filepath} wird bearbeitet...\n{content}")
                return content
        return None


class IceTester:
    def __init__(self, env_cls, lexer, parser):
        self.env = env_cls()
        self.env.builtins()
        self.lexer = lexer
        self.parser = parser

    def test_lexer(self, input_string, verbose=False):
        if input_string is None:
            print("Es ist ein Fehler mit dem InputStream.")
            return False

        self.lexer.input(input_string)
        result = True
        for token in self.lexer:
            if str(token).startswith("LexToken(error"):
                result = False
            if verbose:
                print("Korrekte Assersion: " + str(token))

        if verbose:
            print("done.\n====")
        return result

    def test_parser(self, input_string, verbose=False):
        if input_string is None:
            print("Es ist ein Fehler mit dem InputStream.")
            return False

        try:
            result = self.parser.parse(input_string, debug=DEBUG)
        except Exception as e:
            if verbose:
                print(f"Parser-Fehler: {e}")
            return False
        return result is not None

    def test_interpreter(self, input_string, verbose=False, clear=False):
        if input_string is None:
            print("Es ist ein Fehler mit dem InputStream.")
            return None

        ast = self.parser.parse(input_string, debug=DEBUG)
        if verbose:
            print(input_string, end=" === ")

        result = eval(ast, self.env, verbose)
        if verbose:
            print(result)

        if clear:
            self.env.clear()

        return result


# MAIN
file_manager = IceFileManager()
tester = IceTester(SymbolTable, lexer, parser)

# MEINE SPRACHE SOLL FOLGENDE EIGENSCHAFTEN HABEN #
# ATOMIC
assert tester.test_interpreter("5") == 5
assert tester.test_interpreter("0x5") == 5
assert tester.test_interpreter("0b101") == 5
assert tester.test_interpreter("3.14") == 3.14
# assert not tester.test_parser(".14")
# assert not tester.test_parser("3.")
assert tester.test_interpreter("3 imag") == 3j
assert tester.test_interpreter("(2 + 3) imag") == 5j
assert tester.test_interpreter("2 + 3 imag") == 2 + 3j
assert tester.test_interpreter("(2 + 3) imag + 1") == 1 + 5j
assert tester.test_interpreter("(2 + 3)e 2") == 500
assert tester.test_interpreter("π := 3.1415") == 3.1415

# BINOPS
assert tester.test_interpreter("2 + 3") == 5
assert tester.test_interpreter("7 - 4") == 3
assert tester.test_interpreter("5 * 6") == 30
assert tester.test_interpreter("8 / 2") == 4.0
assert tester.test_interpreter("9 mod 4") == 1
assert tester.test_interpreter("0 mod 1") == 0
try:
    a = tester.test_interpreter("1 mod 0")
    raise Exception("Kein Zero Division Error!")
except ZeroDivisionError:
    pass

assert tester.test_interpreter("2 ** 3") == 8
assert tester.test_interpreter("0 ** 0") == 1
assert tester.test_interpreter("0 ** 1") == 0

assert tester.test_interpreter("7 | 3") == 7 / 3  # normale Division
assert tester.test_interpreter("-7 / 3") == -2  # Aufrunden Minus
assert tester.test_interpreter("7 / 3") == 3  # Aufrunden
assert tester.test_interpreter("-7 \\ 3") == -3  # Abrunden Minus
assert tester.test_interpreter("7 \\ 3") == 2  # Abrunden

assert tester.test_interpreter("3 = 3") == 1
assert tester.test_interpreter("4 > 2") == 1
assert tester.test_interpreter("2 < 5") == 1
assert tester.test_interpreter("4 = 4 != 5") == 1
assert tester.test_interpreter("4 = 4 != 4") == 0
assert tester.test_interpreter("3 = 3 = 3 = 4") == 0
assert tester.test_interpreter("3 = 3 = 3 = 3") == 1
assert tester.test_interpreter("4 > 2 > -2") == 1
assert tester.test_interpreter("2 < 5 < 2 e 10 > 0") == 1
assert tester.test_interpreter("3 != 4") == 1
assert tester.test_interpreter("4 != 4") == 0
assert tester.test_interpreter("5 <= 5") == 1
assert tester.test_interpreter("6 <= 5") == 0
assert tester.test_interpreter("6 >= 5") == 1
assert tester.test_interpreter("{x:=12; 6 >= x}") == 0

# COMPS
assert tester.test_interpreter("1 and 1") == 1
assert tester.test_interpreter("{x:=1; 0 and x}") == 0
assert tester.test_interpreter("{x:=0; 1 or x}") == 1
assert tester.test_interpreter("1 or 0") == 1
assert tester.test_interpreter("1 xor 0") == 1
assert tester.test_interpreter("1 xor 1") == 0
assert tester.test_interpreter("not 1") == 0
assert tester.test_interpreter("not not 1") == 1
assert tester.test_interpreter("not 0") == 1
assert tester.test_interpreter("not (1 and 0)") == 1

# UNARY
assert tester.test_interpreter("-5") == -5
assert tester.test_interpreter("-(+5)") == -5
assert tester.test_interpreter("+5") == 5
assert tester.test_interpreter("-(+(-(-5)))") == -5
assert tester.test_interpreter("+(-5)") == 5
assert tester.test_interpreter("not -1") == 0

# ENVIRONMENT / ASSIGNMENT
assert tester.test_interpreter("a := 7") == 7
assert tester.test_interpreter("a := (x:=2) + 5") == 7
assert tester.test_interpreter("{a:=2; a+:=3; a}") == 5
assert tester.test_interpreter("{a:=2; a-:=5; a}") == -3
assert tester.test_interpreter("{a:=3; a*:=-2; a}") == -6
assert tester.test_interpreter("{a:=4; a/:=2; a}") == 2

# COMPLEX COMPS/BINOPS/UNARY
assert tester.test_interpreter("(2 + -3) * 4") == -4
assert tester.test_interpreter("{2 < 5 <2 e 10 > 0}") == 1
assert tester.test_interpreter("{2 < 5 and 5<2 e 10 and 2e 10 > 0}") == 1
assert tester.test_interpreter("{(2 < 5) and (5<2 e 10) and (2e 10 > 0)}") == 1
assert (
    tester.test_interpreter("{(2 < 5) and (5<2 e 10) and (2e 10 > 5) and (x:=1)}") == 1
)
assert tester.test_interpreter("{x:=2<3; x:=x+1; x}") == 2

test_code = r"""
{
a:=1;
b:=2;
a+:=b * 3;
a
}
"""
assert tester.test_interpreter(test_code) == 7

test_code = r"""
{
x:=0;
x:=x+1;
x:=x+1;
x:=x+1;
x
}
"""
assert tester.test_interpreter(test_code) == 3

test_code = r"""
{
x:=0+3*5-(-3);
x+:=3;
x
}
"""

assert tester.test_interpreter(test_code) == 21

test_code = r"""
{
x:= 21;
x:= -x**3;
x:=-x-2;
x mod 5;
}
"""
assert tester.test_interpreter(test_code) == 4

test_code = r"""
{
x:=3;
y:=5;
(x<y and y>x) or (x=y)
}
"""
assert tester.test_interpreter(test_code) == 1

test_code = r"""
{
z:=0;
x:=1 or (z:=1);
z
}
"""
assert tester.test_interpreter(test_code) == 1  # short-circuit: z bleibt 0

test_code = r"""
{
x:= 21;
x:= -x**3;
x:=-x-2;
x mod 5;
y:=0xff + 0b11 + -x - 5 e 10;
}
"""
assert tester.test_interpreter(test_code) == -50000009001

test_code = r"""
{
x:=-49999999742;
x := 256;
x := x mod 5 \ 4 - 10 ** (4 | 2 + 3) / 5;
i_me:=420.69
}"""
assert tester.test_interpreter(test_code) == 420.69

test_prec = r"""
{
func := lambda i64 x -> 3 + 5 or 7imag ** 2 xor {1 + -10 <= -5} - +12 and 2<3<4<5 and 1 * 9 e (not 1 | 2 mod 5 + 5) / x = 1 \ 5;
y := func(1);
y +:= [1,2];
}
"""

assert tester.test_interpreter(test_prec) == [3, 4]

################### LEXER ###################
################### PARSER ###################
################### INTERPRETER ###################
green = "\001\033[32m\002"
red = "\001\033[31m\002"
normal = "\001\033[0m\002"
state = ["FAILED", "OK"]

for file, content in file_manager.find_files():
    print(f"Teste Datei: {"/".join(str(file).split("/")[-2:])}")

    b = tester.test_lexer(content, verbose=False)
    print(f"{'Lexer':<12} {green if b else red} {state[int(bool(b))]:<10} {normal}")

    b = tester.test_parser(content, verbose=False)
    print(f"{'Parser':<12} {green if b else red} {state[int(bool(b))]:<10} {normal}")

    b = tester.test_interpreter(content, verbose=False)
    print(
        f"{'Interpreter':<12} {green if b else red} {state[int(bool(b))]:<10} {normal}"
    )
