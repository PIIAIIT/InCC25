from test.manager import IceFileManager
from test.tester import IceTester


def simple_tests(tester):
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
    assert tester.test_interpreter("f64 π := 3.1415") == 3.1415

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
    assert tester.test_interpreter("{i64 x:=12; 6 >= x}") == 0

    # COMPS
    assert tester.test_interpreter("1 and 1") == 1
    assert tester.test_interpreter("{i64 x:=1; 0 and x}") == 0
    assert tester.test_interpreter("{i64 x:=0; 1 or x}") == 1
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
    assert tester.test_interpreter("i64 a := 7") == 7
    assert tester.test_interpreter("i64 a := (i64 x:=2) + 5") == 7
    assert tester.test_interpreter("{i64 a:=2; a+:=3; a}") == 5
    assert tester.test_interpreter("{i64 a:=2; a-:=5; a}") == -3
    assert tester.test_interpreter("{i64 a:=3; a*:=-2; a}") == -6
    assert tester.test_interpreter("{i64 a:=4; a/:=2; a}") == 2

    # COMPLEX COMPS/BINOPS/UNARY
    assert tester.test_interpreter("(2 + -3) * 4") == -4
    assert tester.test_interpreter("{2 < 5 <2 e 10 > 0}") == 1
    assert tester.test_interpreter("{2 < 5 and 5<2 e 10 and 2e 10 > 0}") == 1
    assert tester.test_interpreter("{(2 < 5) and (5<2 e 10) and (2e 10 > 0)}") == 1
    assert (
        tester.test_interpreter(
            "{(2 < 5) and (5<2 e 10) and (2e 10 > 5) and (i64 x:=1)}"
        )
        == 1
    )
    assert tester.test_interpreter("{i64 x:=2<3; x:=x+1; x}") == 2

    test_code = r"""
    {
    i64 a:=1;
    i64 b:=2;
    a+:=b * 3;
    a
    }
    """
    assert tester.test_interpreter(test_code) == 7

    test_code = r"""
    {
    i64 x:=0;
    x:=x+1;
    x:=x+1;
    i64 x:=x+1;
    x
    }
    """
    assert tester.test_interpreter(test_code) == 3

    test_code = r"""
    {
    i64 x:=0+3*5-(-3);
    x+:=3;
    x
    }
    """

    assert tester.test_interpreter(test_code) == 21

    test_code = r"""
    {
    i64 x:= 21;
    i64 x:= -x**3;
    i64 x:=-x-2;
    x mod 5;
    }
    """
    assert tester.test_interpreter(test_code) == 4

    test_code = r"""
    {
    i64 x:=3;
    i64 y:=5;
    (x<y and y>x) or (x=y)
    }
    """
    assert tester.test_interpreter(test_code) == 1

    test_code = r"""
    {
    i64 z:=0;
    i64 x:=1 or (z:=1);
    z
    }
    """
    assert tester.test_interpreter(test_code) == 1  # short-circuit: z bleibt 0

    test_code = r"""
    {
    i64 x:= 21;
    x:= -x**3;
    x:=-x-2;
    x mod 5;
    i64 y:=0xff + 0b11 + -x - 5 e 10;
    }
    """
    assert tester.test_interpreter(test_code) == -50000009001

    test_code = r"""
    {
    i64 x:=-49999999742;
    x := 256;
    x := x mod 5 \ 4 - 10 ** (4 | 2 + 3) / 5;
    f64 i_me:=420.69
    }"""
    assert tester.test_interpreter(test_code) == 420.69

    test_prec = r"""
    {
    i64 -> i64 func := lambda i64 x -> i64 : 3 + 5 or 7imag ** 2 xor {1 + -10 <= -5} - +12 and 2<3<4<5 and 1 * 9 e (not 1 | 2 mod 5 + 5) / x = 1 \ 5;
    i64 y := func(1);
    y +:= [1,2];
    }
    """

    assert tester.test_interpreter(test_prec) == [3, 4]


def file_tests(tester):
    ################### LEXER ###################
    ################### PARSER ###################
    ################### INTERPRETER ###################
    green = "\001\033[32m\002"
    red = "\001\033[31m\002"
    normal = "\001\033[0m\002"
    state = ["FAILED", "OK"]

    file_manager = IceFileManager(ignore_dirs={"match", "struct"})
    for file, content in file_manager.find_all_files():
        print(f"Teste Datei: {"/".join(str(file).split("/")[-2:])}")

        b = tester.test_lexer(content, verbose=False)
        print(f"{'Lexer':<12} {green if b else red} {state[int(bool(b))]:<10} {normal}")

        b = tester.test_parser(content, verbose=False)
        print(
            f"{'Parser':<12} {green if b else red} {state[int(bool(b))]:<10} {normal}"
        )

        b = tester.test_interpreter(content, verbose=False)
        print(
            f"{'Interpreter':<12} {green if b else red} {state[int(bool(b))]:<10} {normal}"
        )


def small_file_tests(tester):
    ################### LEXER ###################
    ################### PARSER ###################
    ################### INTERPRETER ###################
    green = "\001\033[32m\002"
    red = "\001\033[31m\002"
    normal = "\001\033[0m\002"
    state = ["FAILED", "OK"]

    file_manager = IceFileManager("small_tests")
    for file, content in file_manager.find_all_files():
        print(f"Teste kleine Datei: {"/".join(str(file).split("/")[-2:])}")

        b = tester.test_lexer(content, verbose=False)
        print(f"{'Lexer':<12} {green if b else red} {state[int(bool(b))]:<10} {normal}")

        b = tester.test_parser(content, verbose=False)
        print(
            f"{'Parser':<12} {green if b else red} {state[int(bool(b))]:<10} {normal}"
        )

        b = tester.test_interpreter(content, verbose=False)
        print(
            f"{'Interpreter':<12} {green if b else red} {state[int(bool(b))]:<10} {normal}"
        )
