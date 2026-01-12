import os
from parser import parser, Node
import numpy as np
from datatypes import (
    Lambda,
    parse_call_arguments,
    Struct,
)
from utils import iter_tuple, binop_for_lists, binop_for_tuples
from environment import SymbolTable

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


def eval(node: Node, env, debug=False):
    match node.ast:
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

        case ("var", n):
            if n not in env:
                raise Exception(f"variable {n} not found in environment")
            return env[n].value

        case ("unary", op, expr):
            x = eval(expr, env)
            return unary_operations[op](x)

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

        case ("assign", _, var, val):
            if not isinstance(var, str):
                raise Exception(f"Expected variable, got {var}")
            y = eval(val, env)
            if var in env:
                env[var].value = y
            else:
                env.define(var, y)
            print("Assign: ", var, val) if debug else ""
            return y

        case ("undef", ("var", var)):
            if var[0] != "var":
                raise Exception(f"Expected variable, got {var}")
            if var in env:
                del env[var]
            else:
                raise Exception(f"variable {var} not found in environment")
            return None

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
            arr: list = eval(interval, env)

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

        case ("lambda", parameter, body, ret_type):
            # Lambda-bjekt mit aktuellem Closure zurückgeben
            return Lambda(parameter, body, env.copy(), ret_type)

        case ("call", func, args_expr):
            pos_arg, key_arg = parse_call_arguments(args_expr, eval, env)

            # Closure
            func_obj = eval(func, env)

            if not callable(func_obj):
                raise TypeError(f"Cannot call object of type {type(func_obj)}")
            return func_obj(pos_arg, key_arg, eval)

        case ("letrec", assignments, body):
            local_env = SymbolTable(parent=env)

            for *_, var, expr in assignments:
                local_env.put(var)

            for assigns in assignments:
                eval(assigns, local_env)

            return eval(body, local_env)

        case ("array", list_elements):
            return [eval(elem, env) for elem in list_elements]

        case ("array_access", array_ptr, index):
            arr = eval(array_ptr, env)
            assert isinstance(
                arr, (list, tuple, str)
            ), f"{type(arr)} {arr} ist nicht veränderlich."

            if index == "+":
                return arr[1:] if isinstance(arr, list) else arr[1]

            i = eval(index, env)
            if isinstance(arr, list):
                return arr[i]
            if isinstance(arr, str):
                return arr[i]

            return list(iter_tuple(arr))[i]

        case ("list", list_elements):
            if len(list_elements) == 0:
                return None
            if len(list_elements) == 1:
                return eval(Node("cons", list_elements[0], Node("leere")), env)
            return eval(
                Node("cons", list_elements[0], Node("list", list_elements[1:])), env
            )

        case ("cons", expr1, expr2):
            a = eval(expr1, env)
            b = eval(expr2, env)
            if isinstance(a, list) and isinstance(b, list):
                return a + b
            return (a, b)

        case ("leere",):
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
            local_env = SymbolTable(parent=env)

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

        case ("access_struct", struct, var_name):
            if var_name[0] != "var":
                raise Exception(f"Expected variable, got {var_name}")
            return eval(struct, env)[var_name[1]]

        case "program", body:
            result = eval(body, env)
            return result
        case _:
            print(f"unknown expression {node}")
            return -1


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
