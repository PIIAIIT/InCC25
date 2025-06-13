from environment import Environment
DEBUG = False


class Lambda:
    """Repräsentiert eine Lambda-Funktion mit Parametern, Defaults und Closure"""

    def __init__(self, params, varargs, defaults, body, closure_env):
        self.params: list = params  # Liste der Parameter-Namen
        self.varargs: str | None = varargs  # Name des varargs Parameters oder None
        self.defaults: dict = defaults  # Dict mit default-Werten
        self.closure_env: Environment = closure_env  # Environment zur Closure-Zeit
        self.body = body  # AST des Lambda-Bodies

    def __repr__(self):
        return "LAMBDA OBJ: {" + str([self.params, *[self.varargs], *[self.defaults.items()]]) + "}"


def parse_lambda_parameters(parameter, eval_func, env):
    """Parst Lambda-Parameter und extrahiert reguläre Parameter, Defaults und Varargs"""
    params = []
    defaults = {}
    varargs = None
    print("DEBUG -- Parse Lambda Parameter") if DEBUG else 0
    # ('parameter', [('pos', 'x'), ('keyword', 'y', ('num', '3')), ('keyword', 'z', ('num', '5')), ('infty', 'c')])
    for param in parameter[1]:
        match param:
            case 'keyword', var, expr:
                defaults[var] = eval_func(expr, env)
            case 'infty', var:
                varargs = var
            case 'pos', var:
                params.append(var)

    return params, defaults, varargs # ['x'] {'y': 3, 'z': 5} c


def parse_call_arguments(args_expr, eval_func, env):
    """Parst Aufruf-Argumente in positionelle und Keyword-Argumente"""
    pos_args = []
    keyword_args = {}
    print("DEBUG -- Parse Call Argumente") if DEBUG else 0
    print("Diese Argumente sollen gecallt werden: ", args_expr, end="") if DEBUG else 0

    for param in args_expr[1]: # [('pos', ('num', '2')), ('keyword', ('var', 'x'), ('num', '3'))]
        match param:
            case 'pos', expr:
                a = eval_func(expr, env)
                pos_args.append(a)
            case 'keyword', var, expr:
                val = eval_func(expr, env)
                keyword_args[var[1]] = val
    print(" und diese kamen raus : ", pos_args, keyword_args) if DEBUG else 0
    return pos_args, keyword_args # [[2], {x:3}]

# f := lambda (x,y:3) -> x-y
def call_lambda(lambda_obj: Lambda, pos_args, keyword_args, eval_func, env):
    """Führt einen Lambda-Ausdruck aus oder erstellt Partial Application"""
    # Lokales Environment mit den Definitions Variblen erstellen mit Wert
    print("DEBUG -- Lokales Environment erstellen") if DEBUG else 0
    print("Das Lambda-Objekt  das gecallt wird : ", lambda_obj) if DEBUG else 0
    # f(y:5)
    lokal_env = Environment(parent=lambda_obj.closure_env)
    lokal_env.put(lambda_obj.params)
    for k, v in lambda_obj.defaults.items():
        lokal_env.put(k)
        lokal_env[k] = v
    if lambda_obj.varargs is not None:
        lokal_env.put([lambda_obj.varargs])
    print("Das Environment von dem Lambda : ", lokal_env) if DEBUG else 0

    print("DEBUG -- Argumente binden") if DEBUG else 0
    new_params = lambda_obj.params.copy()
    new_defaults = lambda_obj.defaults.copy()
    print("NEW PARAMS ", new_params, "NEW DEFAULTS", new_defaults) if DEBUG else 0

    # Zuerst Keyword Args auf lambda env binden
    bound_keys = []
    for k, v in keyword_args.items():
        lokal_env[k] = v
        new_defaults[k] = v
        bound_keys.append(k)
    print("Gebundene Keyword Args: ", new_defaults) if DEBUG else 0

    # Dann Pos Args auf restliche lambda env binden
    for key, val in zip(new_params, pos_args):
        lokal_env[key] = val
        bound_keys.append(key)
    print("Gebundene Positionale Args: ", new_params) if DEBUG else 0

    for key in bound_keys:
        if key in new_params:
            new_params.remove(key)
    # Checken ob Positionale Args alle gebunden sind
    # Wenn nein, return Lambda mit neuem Environment und Parameter
    if new_params: # ist nicht leer
        return Lambda(new_params, lambda_obj.varargs, new_defaults, lambda_obj.body, lokal_env)

    # Wenn ja, execute Lambda
    print("DEBUG -- Execute Lambda") if DEBUG else 0
    return eval_func(lambda_obj.body, lokal_env)

