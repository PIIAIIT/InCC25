from interpreter import eval
from typisierung import typecheck
from zwischencode import free, iic_gen
from maschinecode import maschine_code
import ice2_ws25.ice_machine as ice_machine

DEBUG = False


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

    def test_iic(self, input_string, verbose=False):
        """Integrierter Interpreter-Check: Lexer, Parser, Interpreter"""
        if input_string is None:
            print("Es ist ein Fehler mit dem InputStream.")
            return None

        ast = self.parser.parse(input_string, debug=verbose)
        ast = typecheck(ast, self.env)
        ast = free(ast)

        result = iic_gen(ast)
        regs = ice_machine.run(result, debug=verbose, detailed=verbose)

        print(regs)
        return regs.get("R0", None)

    def test_asm(self, input_string, verbose=False):
        """Integrierter Assembler-Check: Lexer, Parser, Interpreter"""
        if input_string is None:
            print("Es ist ein Fehler mit dem InputStream.")
            return None

        ast = self.parser.parse(input_string, debug=verbose)
        ast = typecheck(ast, self.env)
        ast = free(ast)

        result = iic_gen(ast)
        regs = ice_machine.run(result, debug=verbose, detailed=verbose)

        asm_code = maschine_code(result)

        if verbose:
            print(asm_code)

        return regs.get("R0", None)
