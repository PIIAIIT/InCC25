import numpy as np

bin_operations = {
    "plus": lambda x, y: x + y,
    "minus": lambda x, y: x - y,
    "times": lambda x, y: x * y,
    "divide_ceil": lambda x, y: -(-x // y),
    "divide": lambda x, y: x / y,
    "mod": lambda x, y: x % y,
    "divide_floor": lambda x, y: x // y,
    # booleans
    "and": lambda x, y: int(x and y),
    "or": lambda x, y: int(x or y),
    "xor": lambda x, y: int(x ^ y),
    "equals": lambda x, y: int(x == y),
    "greater_than": lambda x, y: int(x > y),
    "smaller_than": lambda x, y: int(x < y),
    "greater_equals": lambda x, y: int(x >= y),
    "smaller_equals": lambda x, y: int(x <= y),
    "unequals": lambda x, y: int(x != y),
    # exp
    "exp": lambda x, y: x * 10**y,
}

unary_operations = {
    "not": lambda x: int(not x),
    "uminus": lambda x: -x,
    "uplus": lambda x: x if x > 0 else -x,
    "inc": lambda x: x + 1,
    "dec": lambda y: y - 1,
    "imag": lambda x: np.complex64(x),
}


def eval(expression, env):
    match expression:
        case ("num", n):
            if n.startswith("0b"):
                return int(n, 2)
            if n.startswith("0x"):
                return int(n, 16)
            return int(n)
        case ("float", n):
            return float(n)
        case ("complex", re, imag):
            a = eval(re, env)
            b = eval(imag, env)
            return unary_operations["imag"](a, b)
        case ("var", n):
            if n not in env:
                raise Exception(f"variable {n} not found in environment {env}")
            return env[n]

        case ("binop", op, expr1, expr2):
            x = eval(expr1, env)
            y = eval(expr2, env)
            return bin_operations[op](x, y)

        case ("comp", op, x):
            x = [eval(xi, env) for xi in x]
            return int(
                all([bin_operations[op[i]](x[i], x[i + 1]) for i in range(len(op))])
            )

        # case ("comp", seq):
        #     x = eval(left, env)
        #     y = eval(right, env)
        #     return bin_operations[op](x, y)

        case ("power", expr1, expr2):
            x = eval(expr1, env)
            y = eval(expr2, env)
            return x**y

        case ("assign", var, val):
            # if var not in env:
            # raise Exception(f"variable {var} not found in environment {env}")
            env[var] = eval(val, env)
            return env[var]

        case ("postfix", op, var):
            vorerst = eval(var, env)
            env[var] = unary_operations[op](vorerst)
            return env[var]

        case ("unary", op, expr):
            x = eval(expr, env)
            return unary_operations[op](x)

        case ("seq", body):
            for expr in body[:-1]:
                eval(expr, env)
            return eval(body[-1], env)

        case _:
            print(f"unknown expression {expression}")
            return -1
