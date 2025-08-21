import os
from parser import parser
import numpy as np
from datatypes import (
    Lambda,
    parse_call_arguments,
    Struct,
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
    "uplus": lambda x: x if x > 0 else -x,
    "uminus": lambda x: -x,
    "imag": lambda x: np.complex64(0, x),
}


pyeval = eval
loaded_modules = set()


def eval(expression, env: Environment, debug=False):
    match expression:
        case ("num", n):
            base = 10
            if n.startswith("0b"):
                base = 2
            if n.startswith("0x"):
                base = 16
            return int(n, base)
        case ("float", n):
            return float(n)
        case ("str", n):
            return str(n[1:-1])
        case ("complex", imag):
            a = eval(imag, env)
            return unary_operations["imag"](a)
        case ("var", n):
            if n not in env:
                raise Exception(f"variable {n} not found in environment")
            return env[n].value

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
            ops, exprs, tmp = [f], [x], y
            while tmp[0] == "comparison":
                ops.append(tmp[1])
                exprs.append(tmp[2])
                tmp = tmp[3]
            exprs.append(tmp)
            values = [eval(e, env) for e in exprs]
            return int(
                all(
                    [
                        bin_operations[ops[i]](values[i], values[i + 1])
                        for i in range(len(ops))
                    ]
                )
            )

        case ("assign", op, var, val):
            y = eval(val, env)
            print("Assign: ", op, var, val) if debug else ""
            if op is not None:
                y = eval(("binop", op, ("var", var), val), env)

            if var in env:
                env[var].value = y
            else:
                env.define(var, y)
            return y

        case ("unary", op, expr):
            x = eval(expr, env)
            return unary_operations[op](x)

        case ("seq", body):
            if body == []:
                return None
            for e in body[:-1]:
                eval(e, env)
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
                arr = list(iter_tuple(arr))

            local_env = env.push(counter)

            result = None
            for i in arr:
                local_env[counter].value = i
                result = eval(body, local_env)
            return result

        case ("interval", left_interval, expr1, expr2, right_interval):
            a = eval(expr1, env)
            b = eval(expr2, env)
            if not isinstance(a, int) or not isinstance(b, int):
                raise TypeError("Non-Int Type is not supported!")
            a += 1 if left_interval == "]" else 0
            b -= 1 if right_interval == "[" else 0
            return list(range(a, b + 1))

        case ("lambda", parameter, body):
            # Lambda-bjekt mit aktuellem Closure zurückgeben
            return Lambda(parameter, body, env.copy())

        case ("call", func, args_expr):
            pos_arg, key_arg = parse_call_arguments(args_expr, eval, env)

            # Closure
            func_obj = eval(func, env)

            if not callable(func_obj):
                raise TypeError(f"Cannot call object of type {type(func_obj)}")
            return func_obj(pos_arg, key_arg, eval)

        case ("let", assignments, body):
            env2 = Environment(parent=env)

            for _, op, var, val in assignments:
                if op is not None:
                    raise Exception(f"Cannot Operation Assign in a let.")
                env2.put(var)
                obj = eval(("assign", None, var, val), env2)
                if isinstance(obj, Lambda):
                    obj.override_env(env2)

            return eval(body, env2)

        case ("array", list_elements):
            return [eval(elem, env) for elem in list_elements]

        case ("array_access", array_ptr, index):
            arr = eval(array_ptr, env)
            assert isinstance(
                arr, (list, tuple)
            ), f"{type(arr)} {arr} ist nicht veränderlich."

            if index == "+":
                return arr[1:] if isinstance(arr, list) else arr[1]

            i = eval(index, env)  # expression
            if isinstance(arr, list):
                return arr[i]

            return list(iter_tuple(arr))[i]

        case ("list", list_elements):
            if len(list_elements) == 0:
                return None
            if len(list_elements) == 1:
                return eval(("cons", list_elements[0], ("leere")), env)
            return eval(("cons", list_elements[0], ("list", list_elements[1:])), env)

        case ("cons", expr1, expr2):
            a, b = eval(expr1, env), eval(expr2, env)
            if isinstance(a, list) and isinstance(b, list):
                return a + b
            return (a, b)

        case "leere":
            return None

        case ("import", [path]):
            if path in loaded_modules:
                return
            full_path = os.path.join(os.curdir, path)
            if not os.path.exists(full_path):
                raise Exception(f"Es gibt kein Modul mit dem Namen: {path}")
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
            loaded_modules.add(path)
            return eval(parser.parse(code), env)

        case ("match", expr, cases):
            value = eval(expr, env)
            local_env = Environment(parent=env)

            for pattern, body in cases:
                if debug:
                    print("match", value, ": ") if debug else ""
                    print("case", pattern, ": ") if debug else ""
                if pattern[1] == "_" or match_pattern(pattern, value, local_env):
                    return eval(body, local_env)
            return None

        case ("struct", attributes):
            s = Struct()
            for *_, name, expr in attributes:
                s[name] = eval(expr, env)
            return s

        case ("access_struct", struct, ("var", name)):
            return eval(struct, env)[name]

        case _:
            print(f"unknown expression {expression}")
            return -1


def iter_tuple(t):
    while isinstance(t, tuple):
        yield t[0]
        t = t[1]


# PRIVATE FUNKTIONS
def binop_for_lists(x, y, func):
    if isinstance(x, list) or isinstance(y, list):
        return [
            func(i, j)
            for i, j in zip(
                x if isinstance(x, list) else [x] * len(y),
                y if isinstance(y, list) else [y] * len(x),
            )
        ]
    return None


def binop_for_tuples(x, y, func):
    if isinstance(x, tuple) and isinstance(y, tuple):
        # (1, (2, (3, None))) + (2, (3, (4, None)))
        a = x[0] if isinstance(x, tuple) else x
        b = y[0] if isinstance(y, tuple) else y

        if a is None or b is None:
            return y if b is None else x

        next_x = x[1] if isinstance(x, tuple) and x[1] is not None else None
        next_y = y[1] if isinstance(y, tuple) and y[1] is not None else None

        next_pair = binop_for_tuples(next_x, next_y, func) if next_x or next_y else None
        return (func(a, b), next_pair)
    if isinstance(x, tuple) or isinstance(y, tuple):
        # (1, (2, (3, None))) + 2
        # 2 + (1, (2, (3, None)))
        a = x[0] if isinstance(x, tuple) else y[0]
        b = x if not isinstance(x, tuple) else y

        next = (
            x[1]
            if isinstance(x, tuple) and x[1] is not None
            else y[1] if isinstance(y, tuple) and y[1] is not None else None
        )

        next_pair = binop_for_tuples(next, b, func) if next else None
        return (func(a, b), next_pair)

    return None


def match_pattern(pattern, value, env):
    """
    Versucht, das Pattern auf den Wert zu matchen.
    `pattern`: Das Pattern, z. B. ['list', ['a', 'b']]
    `value`: Das zu matchende Python-Objekt, z. B. [1, 2]
    `env`: Dictionary, das gebundene Variablen aufnimmt.
    Rückgabe: True, wenn das Pattern matched, False sonst.
    """
    kind = pattern[0]

    # Literal (int, float, str, complex)
    if kind in ("num", "str", "float", "complex"):
        return eval(pattern, env) == value

    if kind == "var":
        env.define(pattern[1], value)
        return True

    # pattern: ['list', [p1, p2, p3]]
    # value: (p1, (p2, (p3, None)))
    if kind == "list":
        subpatterns = pattern[1]
        list_len = sum(1 for _ in iter_tuple(value))
        if not isinstance(value, tuple) or len(subpatterns) != list_len:
            return False
        return all(
            match_pattern(p, v, env) for p, v in zip(subpatterns, iter_tuple(value))
        )

    # Tuple: ['array', [(var, a), (num, 3), (var, c)]]
    # value: [1, 2, 3]
    if kind == "array":
        subpatterns = pattern[1]
        if not isinstance(value, list) or len(subpatterns) != len(value):
            return False
        return all(match_pattern(v, p, env) for v, p in zip(subpatterns, value))

    # Struct: ['struct', [('a', '123'), ('b', 'x')]]
    # value: {a: 123, b : 5}
    if kind == "struct":
        subpatterns = pattern[1]
        if not isinstance(value, dict):  # or len(subpatterns) != len(value):
            return False
        for *_, key, subp in subpatterns:
            if key not in value or not match_pattern(subp, value[key], env):
                return False
        return True

    return False
