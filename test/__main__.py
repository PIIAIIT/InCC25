from lexer import lexer
from parser import parser
from environment import SymbolTable
from test.tester import IceTester
from test.manager import IceFileManager
from test.examples import simple_tests, file_tests, small_file_tests

# MAIN
tester = IceTester(SymbolTable, lexer, parser)
simple_tests(tester)
file_tests(tester)
# small_file_tests(tester)
