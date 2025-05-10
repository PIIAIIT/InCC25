python_env = python3

default:
	$(python_env) main.py

test: 
	$(python_env) -m test.test

clean:
	rm -f parsertab.py parser.out
