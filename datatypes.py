from environment import SymbolTable
from numpy import complex64

DEBUG = False


########## LABMDA ##########
class Lambda:
    """Repräsentiert eine Lambda-Funktion mit Parametern, Defaults und Closure"""

    def __init__(self, parameter, body, closure_env):
        self.params, self.defaults, self.varargs = parse_lambda_parameters(parameter)
        self.closure_env: SymbolTable = closure_env  # Environment zur Closure-Zeit
        self.body = body  # AST des Lambda-Bodies

    def __repr__(self):
        return f"<Lambda params={self.params}, defaults={list(self.defaults.keys())}, varargs={self.varargs}>"

    def override_env(self, env):
        self.closure_env = env

    def __call__(self, pos_args, keyword_args, eval_func):
        """Führt einen Lambda-Ausdruck aus oder erstellt Partial Application"""
        # Lokales Environment mit den Definitions Variblen erstellen mit Wert
        if DEBUG:
            print("DEBUG -- Lokales Environment erstellen")
            print("Das Lambda-Objekt  das gecallt wird : ", self)

        lokal_env = SymbolTable(parent=self.closure_env)
        for k, v in self.defaults.items():
            lokal_env.put(k)
            if isinstance(v, (tuple, list, dict)):
                lokal_env.define(k, eval_func(v, lokal_env))
            else:
                lokal_env.define(k, v)

        lokal_env.put(self.params)
        if self.varargs:
            lokal_env.put([self.varargs])

        if DEBUG:
            print("Das Environment von dem Lambda : ", lokal_env)
            print("DEBUG -- Argumente binden")

        new_params = self.params.copy()
        new_defaults = self.defaults.copy()
        bound_keys = []

        # Zuerst Keyword Args auf lambda env binden
        for k, v in keyword_args.items():
            if k not in lokal_env:
                raise Exception("Invalid Argument Exception")
            lokal_env.define(k, v)
            new_defaults[k] = v
            bound_keys.append(k)

        if DEBUG:
            print("NEW PARAMS ", new_params, "NEW DEFAULTS", new_defaults)
            print(f"Positional Args:{pos_args}")

        # Dann Pos Args auf restliche lambda env binden
        all_param_names = new_params + list(new_defaults.keys())
        for key, val in zip(all_param_names, pos_args):
            lokal_env.define(key, val)
            bound_keys.append(key)

        if DEBUG:
            print("Gebundene Positionale Args: ", bound_keys)

        for key in bound_keys:
            if key in new_params:
                new_params.remove(key)

        # Checken ob Positionale Args alle gebunden sind
        # Wenn nein, return Lambda mit neuem Environment und Parameter
        if new_params:  # nicht leer
            # [('pos', _, 'x'), ('keyword', _, 'y', ('num', '3')), ('keyword', 'z', ('num', '5')), ('infty', _, 'c')]
            new_parameter = [
                *[("pos", "", x) for x in new_params],
                *[("keyword", "", x, y) for x, y in new_defaults.items()],
            ]
            if self.varargs:
                new_parameter.append(("infty", self.varargs))
            return Lambda(new_parameter, self.body, lokal_env)

        # varargs Belegen
        if self.varargs:
            lokal_env.define(self.varargs, pos_args[len(self.params) :])

        # Wenn ja, execute Lambda
        if DEBUG:
            print("DEBUG -- Execute Lambda")
        # print(lokal_env)

        return eval_func(self.body, lokal_env)


def parse_lambda_parameters(parameter: list) -> tuple[list, dict, None | str]:
    """Parst Lambda-Parameter und extrahiert reguläre Parameter, Defaults und Varargs"""
    params = []
    defaults = {}
    varargs = None
    print("DEBUG -- Parse Lambda Parameter") if DEBUG else 0
    # [('pos', 'x'), ('keyword', 'y', ('num', '3')), ('keyword', 'z', ('num', '5')), ('infty', 'c')]
    for param in parameter:
        match param:
            case ("pos", _, var):
                params.append(var)
            case ("keyword", _, var, expr):
                defaults[var] = expr
            case ("infty", _, var):
                varargs = var
            case _:
                raise Exception(f"Unbekannter Parameter-Typ: {param}")

    return params, defaults, varargs


def parse_call_arguments(args_expr, eval_func, env) -> tuple[list, dict]:
    """Parst Aufruf-Argumente in positionelle und Keyword-Argumente"""
    pos_args = []
    keyword_args = {}
    if DEBUG:
        print("DEBUG -- Parse Call Argumente")
        print("Diese Argumente sollen gecallt werden: ", args_expr, end="")

    # [('pos', ('num', '2')), ('keyword', ('var', 'x'), ('num', '3'))]
    for param in args_expr:
        match param:
            case ("pos", expr):
                pos_args.append(eval_func(expr, env))
            case ("keyword", var, expr):
                keyword_args[var[1]] = eval_func(expr, env)
            case _:
                raise Exception(f"Ungültiges Argumentformat: {param}")
    if DEBUG:
        print(" und diese kamen raus : ", pos_args, keyword_args)
    return pos_args, keyword_args


########## STRUCT ##########
class Struct(dict):
    def __init__(self):
        super().__init__()

    def __repr__(self):
        return "{" + "; ".join([f"{key}: {val}" for key, val in self.items()]) + "}"
