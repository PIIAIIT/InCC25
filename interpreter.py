import os
from parser import parser
import numpy as np

from _lambda import (
    Lambda,
    call_lambda,
    parse_call_arguments,
    parse_lambda_parameters,
)
from environment import Environment

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
    "uminus": lambda x: -x,
    "imag": lambda x: np.complex64(0, x),
}


pyeval = eval
loaded_modules = set()


def eval(expression, env: Environment, debug=False):
    match expression:
        case ("num", n):
            print("num", n) if debug else ""
            if n.startswith("0b"):
                print("num", int(n, 2)) if debug else ""
                return int(n, 2)
            if n.startswith("0x"):
                print("num", int(n, 16)) if debug else ""
                return int(n, 16)
            return int(n)
        case ("float", n):
            print("float", n) if debug else ""
            return float(n)
        case ("str", n):
            print("str", n) if debug else ""
            return str(n[1:-1])
        case ("complex", imag):
            print("complex", imag) if debug else ""
            a = eval(imag, env)
            return unary_operations["imag"](a)
        case ("var", n):
            print("var", n) if debug else ""
            if n not in env:
                raise Exception(f"variable {n} not found in environment {env}")
            return env[n]

        case ("binop", op, expr1, expr2):
            x = eval(expr1, env)
            y = eval(expr2, env)
            func = bin_operations[op]
            if (res := binop_for_lists(x, y, func)) is not None:
                return res
            elif (res := binop_for_tuples(x, y, func)) is not None:
                return res
            return func(x, y)

        case ("comparison", f, x, y):
            ops = [f]
            exprs = [x]
            tmp = y
            while tmp[0] == 'comparison':
                ops.append(tmp[1])
                exprs.append(tmp[2])
                tmp = tmp[3]
            exprs.append(tmp)
            values = [eval(e, env) for e in exprs]
            return int(all([bin_operations[ops[i]](values[i], values[i+1]) for i in range(len(ops))]))

        case ("assign", op, var, val):
            y = eval(val, env)
            if op is not None:
                if debug:
                    print("Assign: ", op, var, val)
                env[var] = eval(("binop", op, ("var", var), val), env)
            else:
                env[var] = y
            return env[var]

        case ("unary", op, expr):
            x = eval(expr, env)
            return unary_operations[op](x)

        case ("seq", body):
            if body == []:
                return None
            for expr in body[:-1]:
                eval(expr, env)
            return eval(body[-1], env)

        case ("if", condition, then_body, else_body):
            if eval(condition, env):
                # statements handling
                return eval(then_body, env)

            if else_body is not None:  # Fall kein else
                for cond, statement in else_body:
                    if cond == "else":
                        return eval(statement, env)
                    elif eval(cond, env):
                        return eval(statement, env)
            # falls if übersprungen wird
            return None

        case ("while", condition, body):
            result = None
            while eval(condition, env):
                result = eval(body, env)
            return result

        case ("loop", counter, interval, body):
            arr = eval(interval, env)

            # Normalisiere das arr zu einem Iterierbaren Objekt
            if isinstance(arr, tuple):
                res_list = []
                tmp = arr # (2, (3, (4, None)))
                while tmp is not None and isinstance(tmp, tuple):
                    res_list.append(tmp[0])
                    tmp = tmp[1]
                arr = res_list

            local_env = Environment(env)
            local_env.put(counter)
            result = None
            for i in arr:
                local_env[counter] = i
                result = eval(body, local_env)
            return result

        case ("interval", left_interval, expr1, expr2, right_interval):
            a = eval(expr1, env)
            b = eval(expr2, env)
            if not isinstance(a, int) or not isinstance(b, int):
                raise TypeError("Non-Int Type is not supported!")
            a += 1 if left_interval == "]" else 0
            b -= 1 if right_interval == "[" else 0
            return range(a, b+1)

        case ("lambda", parameter, body):
            params, defaults, varargs = parse_lambda_parameters(parameter, eval, env)
            return Lambda(params, varargs, defaults, body, env)

        case ("call", func, args_expr):
            func_obj = eval(func, env)

            pos_arg, key_arg = parse_call_arguments(args_expr, eval, env)

            # Fall 1: eigene Lambda-Funktionen
            if isinstance(func_obj, Lambda):
                return call_lambda(func_obj, pos_arg, key_arg, eval, env)
            # Fall 2: Python-Built-in (z.B als Funktion mit __call__)
            elif callable(func_obj):
                print("CALL", func_obj, args_expr) if debug else ""
                return func_obj(pos_arg, key_arg)
            else:
                raise TypeError(f"Cannot call object of type {type(func_obj)}")

        case ("let", assignments, body):
            env2 = Environment(env)
            for _, op, var, val in assignments:
                env2.put(var)
                eval(("assign", op, var, val), env2)
            return eval(body, env2)

        case ("array", list_elements):
            return [eval(elem, env) for elem in list_elements]

        case ("array_access", array_ptr, index):
            arr = eval(array_ptr, env)

            if isinstance(arr, tuple):
                match index:
                    case '+':
                        return arr[1]
                    case _:
                        i = eval(index, env)
                        tmp = arr
                        for _ in range(i):
                            if tmp[1] is None:
                                raise IndexError("Index out of Bounds")
                            tmp = tmp[1]
                        return tmp[0]
            elif isinstance(arr, list):
                match index:
                    case '+':
                        return arr[1:]
                    case _:
                        return arr[eval(index, env)]
            else:
                raise Exception(f"{type(arr)} {arr} ist nicht veränderlich.")

        case ("list", list_elements):
            if len(list_elements) == 0:
                return (None)
            if len(list_elements) == 1:
                return eval(("cons", list_elements[0], ("leere")), env)
            return eval(("cons", list_elements[0], ("list", list_elements[1:])), env)

        case ("cons", expr1, expr2):
            a, b = eval(expr1, env), eval(expr2, env)
            if isinstance(a, list) and isinstance(b, list):
                return a+b
            return (a, b)

        case ("leere"):
            return None

        case ("import", packages):
            # for file in packages[:-1]:
            #     if file not in loaded_modules:
            #         if not os.path.exists(os.path.curdir + "/" + file):
            #             raise Exception(errmsg(file))
            #         with open(file, "r", encoding="utf-8") as f:
            #             code = f.read()
            #         res = parser.parse(code)
            #         loaded_modules.add(file)
            #         eval(res, env)
            #
            path = packages[0]
            if path not in loaded_modules:
                if not os.path.exists(os.path.curdir + "/" + path):
                    raise Exception(f"Es gibt kein Modul mit dem Namen: {path}")
                with open(path, "r", encoding="utf-8") as f:
                    code = f.read()
                loaded_modules.add(path)
                res = parser.parse(code)
                return eval(res, env)

        case ("match", expr, cases):
            expr = eval(expr, env)

            lokal_env = Environment(parent=env)
            for c_expr, c_body in cases[:-1]:
                print("match", expr, ": ") if debug else ""
                print("case", c_expr, ": ") if debug else ""
                if match_pattern(c_expr, expr, lokal_env):
                    return eval(c_body, lokal_env)

            last_case, last_body = cases[-1]
            if last_case[1] == "_":
                return eval(last_body, lokal_env)
            elif match_pattern(last_case, expr, lokal_env):
                print("match", expr, ": ") if debug else ""
                print("case", last_case, ": ") if debug else ""
                return eval(last_body, lokal_env)
            return None

        case ("struct", attributes):
            s = {}
            for _, _, name, expr in attributes:
                s[name] = eval(expr, env)
            return s

        case ("access_struct", struct, name):
            return eval(struct, env)[name]

        case _:
            print(f"unknown expression {expression}")
            return -1


# PRIVATE FUNKTIONS
def binop_for_lists(x, y, func):
    if isinstance(x, list) and isinstance(y, list):
        return [func(i, j) for i, j in zip(x, y)]
    elif isinstance(x, list):
        return [func(i, y) for i in x]
    elif isinstance(y, list):
        return [func(x, i) for i in y]
    return None


def binop_for_tuples(x, y, func):
    if isinstance(x, tuple) and isinstance(y, tuple):
        def inner(ls1, ls2):
            a, b = ls1[0], ls2[0]
            if a is None or b is None:
                return ls2 if b is None else ls1
            if ls1[1] is None or ls2[1] is None:
                return (func(a, b), None)
            return (func(a, b), inner(ls1[1], ls2[1]))
        return inner(x, y)
    elif isinstance(x, tuple):
        def inner2(ls1, y):
            a = ls1[0]
            if a is None:
                return ls1
            if ls1[1] is None:
                return (func(a, y), None)
            return (func(a, y), inner2(ls1[1], y))
        return inner2(x, y)
    elif isinstance(y, tuple):
        def inner3(x, ls2):
            a = ls2[0]
            if a is None:
                return ls2
            if ls2[1] is None:
                return (func(x, a), None)
            return (func(x, a), inner3(x, ls2[1]))
        return inner3(x, y)
    return None


def match_pattern(pattern, value, env):
    """
    Versucht, das Pattern auf den Wert zu matchen.
    `pattern`: Das Pattern, z. B. ['list', ['a', 'b']]
    `value`: Das zu matchende Python-Objekt, z. B. [1, 2]
    `env`: Dictionary, das gebundene Variablen aufnimmt.
    Rückgabe: True, wenn das Pattern matched, False sonst.
    """

    # Literal (int, float, str, complex)
    # ("num", "2")
    # ("str", "'Hello'")
    # ("float", "3.14")
    # ("complex", "3 + 2j")
    if pattern[0] in ["num", "str", "float", "complex"]:
        return eval(pattern, env) == value

    if pattern[0] == "var":
        env[pattern[1]] = value
        return True

    # Liste: ['list', [p1, p2, p3]]
    # value: (p1, (p2, (p3, None)))
    if pattern and pattern[0] == 'list':
        subpatterns = pattern[1]
        list_len = lambda lst : 1 if lst[1] is None else 1 + list_len(lst[1])
        if not isinstance(value, tuple) or len(subpatterns) != list_len(value):
            return False
        for subp, subv in zip(subpatterns, value):
            if not match_pattern(subp, subv, env):
                return False
        return True

    # Tuple: ['array', [(var, a), (num, 3), (var, c)]]
    # value: [1, 2, 3]
    if pattern and pattern[0] == 'array':
        subpatterns = pattern[1]
        if not isinstance(value, list) or len(subpatterns) != len(value):
            return False
        for subp, subv in zip(subpatterns, value):
            if not match_pattern(subp, subv, env):
                return False
        return True

    # Struct: ['struct', [('a', '123'), ('b', 'x')]]
    # value: {a: 123, b : 5} .
    if pattern and pattern[0] == 'struct':
        subpatterns = pattern[1]
        if not isinstance(value, dict) or len(subpatterns) != len(value):
            return False
        for _, _, key, subp in subpatterns:
            if key not in value:
                return False
            if not match_pattern(subp, value[key], env):
                return False
        return True

    return False

