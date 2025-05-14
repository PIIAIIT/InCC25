import numpy as np

bin_operations = {
    "plus": lambda x, y: x + y,
    "minus": lambda x, y: x - y,
    "times": lambda x, y: x * y,
    "power": lambda x, y: x**y,
    "divide": lambda x, y: x / y,
    "divide_floor": lambda x, y: x // y,
    "divide_ceil": lambda x, y: -(-x // y),
    "mod": lambda x, y: x % y,
    "exp": lambda x, y: x * 10**y,
    # booleans
    "and": lambda x, y: bool(x) * bool(y),
    "or": lambda x, y: bool(x) + bool(y),
    "xor": lambda x, y: +bool(bool(x) - bool(y)),
    "equals": lambda x, y: int(x == y),
    "greater_than": lambda x, y: int(x > y),
    "smaller_than": lambda x, y: int(x < y),
    "greater_equals": lambda x, y: int(x >= y),
    "smaller_equals": lambda x, y: int(x <= y),
    "unequals": lambda x, y: int(x != y),
}

unary_operations = {
    "not": lambda x: int(not x),
    "uplus": lambda x: np.abs(x),
    "uminus": lambda x: -x if x > 0 else x,
    "imag": lambda x: np.complex64(0, x),
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
        case ("complex", imag):
            a = eval(imag, env)
            return unary_operations["imag"](a)
        case ("var", n):
            if n not in env:
                raise Exception(f"variable {n} not found in environment {env}")
            return env[n]

        case ("binop", op, expr1, expr2):
            x = eval(expr1, env)
            y = eval(expr2, env)
            return bin_operations[op](x, y)

        case ("comparison_chain", expr1, chain):
            x = eval(expr1, env)
            result = True
            for op, expr2 in chain:
                y = eval(expr2, env)
                result = result and bin_operations[op](x, y)
                x = y
            return result

        case ("comparison_chain", op, expr1, expr2):
            x = eval(expr1, env)
            y = eval(expr2, env)
            return bin_operations[op](x, y)

        case ("assign", var, val):
            env[var] = eval(val, env)
            return env[var]

        case ("assign", op, var, val):
            y = eval(val, env)
            env[var] = bin_operations[op](env[var], y)
            return env[var]

        case ("unary", op, expr):
            x = eval(expr, env)
            return unary_operations[op](x)

        case ("seq", body):
            for expr in body[:-1]:
                eval(expr, env)
            return eval(body[-1], env)

        case ("if", condition, then_body, else_body):
            if else_body is None:
                if eval(condition, env) == 1:
                    return eval(then_body, env)
                else:
                    return None
            elif isinstance(else_body[0], tuple):
                if eval(condition, env) == 1:
                    return eval(then_body, env)
                for cond, statements in else_body:
                    if eval(cond, env) == 1:
                        return eval(statements, env)
            else:
                if eval(condition, env) == 1:
                    return eval(then_body, env)
                return eval(else_body, env)

            # Sem(if expr0: expr1 else expr2, U;S) = (x, S'')
            # wobei (b,S')=Sem(expr0, U;S)
            #
            # (x,S") = Sem(expr1, U;S') falls b=true
            #           Sem(expr2, U;S') sonst

        case ("while", condition, body):
            result = None
            while eval(condition, env):
                result = eval(body, env)
                return result

            # Sem(while cond: expr, U;S) = (x,S")     ,falls n!=0
            #                            = (None,S")  ,sonst
            # (x,S') = Sem(begin cond; expr end, U)^n(S)
            # (t,S") = Sem(cond, U;S') , t=False und n die kleinste Zahl mit dieser Eigenschaft
            # (n,S') = Sem(expr1, U;S)

        case ("loop", counter, interval, body):
            i = env[counter] = 0  # assign a new variable

            links, a, b, rechts = interval
            a, b = eval(a, env), eval(b, env)  # als Zahl evaluieren
            # als nartürliche Zahl evaluieren
            a = a // 1
            b = b // 1
            a += 1 if links == "]" else 0
            b -= 1 if rechts == "[" else 0
            # a=0, b=5
            # [a,b] == [0,..,5]
            # ]a,b] == [1,..,5]
            # [a,b[ == [0,..,4]
            # ]a,b[ == [1,..,4]

            result = None
            for i in range(a, b):
                i += 1
                result = eval(body, env)
            return result

            # Sem(loop expr1: expr2, U;S) = (None, S')          falls n=0
            #                             = Sem(expr2, U)^n(S') sonst

        case _:
            print(f"unknown expression {expression}")
            return -1
