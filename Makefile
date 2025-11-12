PYTHON_ENV = python3

main_file = main.py
lexer_file = lexer.py
parser_file = parser.py

default:
	$(PYTHON_ENV) $(main_file)

lexer:
	$(PYTHON_ENV) $(lexer_file)

parser:
	$(PYTHON_ENV) $(parser_file)

test:
	$(PYTHON_ENV) -m test.test

iic:
	$(PYTHON_ENV) $(main_file) -iic

asm: out.asm
	nasm -f elf64 -o out.o out.asm
	ld -o test.exe out.o
	-./test.exe

debug:
	$(PYTHON_ENV) $(main_file) -debug

clean:
	rm -f parsertab.py parser.out out.asm out.o test.exe __pycache__/*.pyc
