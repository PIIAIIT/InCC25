import numpy as np
from environment import Environment
from _lambda import (
    Lambda,
    call_lambda,
    parse_call_arguments,
    parse_lambda_parameters,
)

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


def eval(expression, env: Environment):
    match expression:
        case ("num", n):
            if n.startswith("0b"):
                return int(n, 2)
            if n.startswith("0x"):
                return int(n, 16)
            return int(n)
        case ("float", n):
            return float(n)
        case ("str", n):
            return str(n)
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

        case ("comparison", f, x, y):
            ops = []
            expr1 = []
            expr2 = []
            ops.append(f)
            expr1.append(x)
            tmp = y
            while tmp[0] == 'comparison':
                ops.append(tmp[1])
                expr2.append(tmp[2])
                expr1.append(tmp[2])
                tmp = tmp[3]
            expr2.append(tmp)
            return int(all([bin_operations[ops[i]](eval(expr1[i], env), eval(expr2[i], env)) for i in range(len(ops))]))

        case ("assign", op, var, val):
            y = eval(val, env)
            if op is not None:
                env[var] = bin_operations[op](env[var], y)
            else:
                env[var] = y
            return env[var]

        case ("unary", op, expr):
            x = eval(expr, env)
            return unary_operations[op](x)

        case ("seq", body):
            for expr in body[:-1]:
                eval(expr, env)
            return eval(body[-1], env)

        case ("if", condition, then_body, else_body):
            if else_body is None:  # Fall kein else
                if eval(condition, env) == 1:
                    # statements handling
                    return eval(("seq", then_body), env)
                    for expr in then_body[:-1]:
                        eval(expr, env)
                    return eval(then_body[-1], env)
                else:
                    return None
            else:
                for cond, statement in else_body:
                    if cond == "None":
                        return eval(("seq", statement), env)
                        for expr in statement[:-1]:
                            eval(expr, env)
                        return eval(statement[-1], env)
                    elif eval(cond, env):
                        return eval(("seq", statement), env)
                        for expr in statement[:-1]:
                            eval(expr, env)
                        return eval(statement[-1], env)
                return None

        case ("while", condition, body):
            result = None
            while eval(condition, env):
                result = eval(("seq", body), env)
            return result

        case ("loop", counter, interval, body):
            left_interval, expr1, expr2, right_interval = interval

            a = eval(expr1, env)
            b = eval(expr2, env)
            if not isinstance(a, int) or not isinstance(b, int):
                raise TypeError("Non-Int Type is not supported!")
            a += 1 if left_interval == "]" else 0
            b -= 1 if right_interval == "[" else 0

            env[counter] = a
            result = None
            while env[counter] < b:
                env[counter] += 1
                result = eval(("seq", body), env)
                # for _b in body:
                #     result = eval(_b, env)
            return result

        case ("lambda", parameter, body):
            params, defaults, varargs = parse_lambda_parameters(parameter, eval, env)
            # print("Lambda-Def: ", params, defaults, varargs)
            return Lambda(params, varargs, defaults, body, env)

        case ("call", func, args_expr):
            func_obj = eval(func, env)
            # print("Dieses Lambda wird gecallt: ", func_obj)

            if isinstance(func_obj, Lambda):
                pos_arg, key_arg = parse_call_arguments(args_expr, eval, env)
                # print("Diese Argumenten wurden geparst", pos_arg, key_arg)
                return call_lambda(func_obj, pos_arg, key_arg, eval, env)

            else:
                # Alter Code für Kompatibilität (falls noch andere Funktionstypen verwendet werden)
                raise TypeError(f"Cannot call object of type {type(func_obj)}")

        case ("let", ("assign", op, var, val) as asgn, body):
            env2 = Environment(env)
            env2.put(var)
            eval(asgn, env2)
            return eval(body, env2)

        case ("function", func, params):
            a = []
            for expr in params:
                a.append(eval(expr, env))
            return eval(func_list[func](a), env)

        case ("array", list_elements):
            arr = []
            for elem in list_elements:
                a = eval(elem, env)
                arr.append(a)
            return arr

        case ("array_access", array_ptr, index):
            arr = eval(array_ptr, env)
            if index == ".":
                return arr[0]
            elif index == "*":
                if len(arr) == 2:
                    return arr[1]
                return arr[1:]
            else:
                i = eval(index, env)
                return arr[i]

        case ("list", list_elements):
            # anonyme lambda func
            return eval(
                    ("cons", list_elements[0], ("list", list_elements[1:])) if len(list_elements) > 0 else ("leere"), env
            )

        case ("cons", expr1, expr2):
            return eval(expr1, env), eval(expr2, env)

        case ("leere"):
            return None

        case _:
            print(f"unknown expression {expression}")
            return -1


def __länge(lst):
    """ Länge einer Liste/Array bestimmen"""
    if len(lst) != 1: 
        raise Exception("")
    if not isinstance(lst[0], list):
        raise Exception("")
    return ("num", str(len(lst[0])))


def __echo(*lst):
    print(lst)
    return ("leere")


def __list(param):
   return ("list", param)


func_list = {
    "echo": __echo,
    "länge": __länge,
    "list": __list,
}
