import numpy as np
from environment import Environment
from _lambda import (
    Lambda,
    PartialApplication,
    call_lambda,
    call_partial_application,
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
                    for expr in then_body[:-1]:
                        eval(expr, env)
                    return eval(then_body[-1], env)
                else:
                    return None
            else:
                for cond, statement in else_body:
                    if cond == "None":
                        for expr in statement[:-1]:
                            eval(expr, env)
                        return eval(statement[-1], env)
                    if eval(cond, env):
                        for expr in statement[:-1]:
                            eval(expr, env)
                        return eval(statement[-1], env)
                return None

        # Sem(if expr0: expr1 else expr2, U;S) = (x, S'')
        # wobei (b,S')=Sem(expr0, U;S)
        #
        # (x,S") = Sem(expr1, U;S') falls b=true
        #           Sem(expr2, U;S') sonst

        case ("while", condition, body):
            result = None
            while eval(condition, env):
                for b in body:
                    result = eval(b, env)
            return result

        # Sem(while cond: expr, U;S) = (x,S")     ,falls n!=0
        #                            = (None,S")  ,sonst
        # (x,S') = Sem(begin cond; expr end, U)^n(S)
        # (t,S") = Sem(cond, U;S') , t=False und n die kleinste Zahl mit dieser Eigenschaft
        # (n,S') = Sem(expr1, U;S)

        case ("loop", counter, interval, body):
            left_interval, expr1, expr2, right_interval = interval

            a = eval(expr1, env)
            b = eval(expr2, env)
            if isinstance(a, float) or isinstance(b, float):
                raise TypeError("Float Type is not supported!")
            a += 1 if left_interval == "]" else 0
            b -= 1 if right_interval == "[" else 0

            env[counter] = a
            result = None
            while env[counter] < b:
                env[counter] += 1
                for _b in body:
                    result = eval(_b, env)
            return result

        # Sem(loop expr1: expr2, U;S) = (None, S')          falls n=0
        #                             = Sem(expr2, U)^n(S') sonst
        case ("lambda", parameter, body):
            params, defauls, varargs = parse_lambda_parameters(parameter, eval, env)
            return Lambda(params, varargs, defauls, body, env)

        case ("call", func, args_expr):
            func_obj = eval(func, env)

            if isinstance(func_obj, Lambda):
                pos_arg, key_arg = parse_call_arguments(args_expr, eval, env)
                return call_lambda(func_obj, pos_arg, key_arg, eval, env)

            elif isinstance(func_obj, PartialApplication):
                pos_arg, key_arg = parse_call_arguments(args_expr, eval, env)
                return call_partial_application(func_obj, pos_arg, key_arg, eval, env)

            else:
                # Alter Code für Kompatibilität (falls noch andere Funktionstypen verwendet werden)
                raise TypeError(f"Cannot call object of type {type(func_obj)}")

        case ("let", ("assign", op, var, val) as asgn, expr):
            env2 = Environment(env)
            env2.put(var)
            eval(asgn, env2)
            return eval(expr, env2)

        case ("function", func, expr):
            if func == "echo":
                a = eval(expr, env)
                if a is not None:
                    print(eval(expr, env))
                    return 1
                return 0
            elif func == "länge":
                a = eval(expr, env)
                if a is not None:
                    return len(a)
                return None

        case _:
            print(f"unknown expression {expression}")
            return -1
