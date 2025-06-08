from environment import Environment


class Lambda:
    """Repräsentiert eine Lambda-Funktion mit Parametern, Defaults und Closure"""

    def __init__(self, params, varargs, defaults, body, closure_env):
        self.params = params  # Liste der Parameter-Namen
        self.varargs = varargs  # Name des varargs Parameters oder None
        self.defaults = defaults  # Dict mit default-Werten
        self.body = body  # AST des Lambda-Bodies
        self.closure_env = closure_env  # Environment zur Closure-Zeit

    def __repr__(self):
        return str(self.params) + str(self.body) + str(self.closure_env)


class PartialApplication:
    """Repräsentiert eine teilweise angewendete Lambda-Funktion"""

    def __init__(self, original_lambda, bound_args):
        self.original_lambda = original_lambda  # ref auf Lambda
        self.bound_args = bound_args  # Dict mit bereits gebundenen Argumenten


def parse_lambda_parameters(parameter, eval_func, env):
    """Parst Lambda-Parameter und extrahiert reguläre Parameter, Defaults und Varargs"""
    params = []
    defaults = {}
    varargs = None

    match parameter:
        case ("parameter", param_list):
            for param in param_list:
                if isinstance(param, list):
                    # Keyword/default Parameter und varargs
                    for item in param:
                        match item:
                            case ("keyword", name, default_expr):
                                params.append(name)
                                defaults[name] = eval_func(default_expr, env)
                            case ("infty", name):
                                varargs = name
                else:
                    # Regulärer positionaler Parameter
                    params.append(param)

    return params, defaults, varargs


def parse_call_arguments(args_expr, eval_func, env):
    """Parst Aufruf-Argumente in positionelle und Keyword-Argumente"""
    pos_args = []
    keyword_args = {}

    match args_expr:
        case ("parameter_expr", arg_list):
            for arg in arg_list:
                if isinstance(arg, list):
                    # Keyword-Argumente
                    for keyword_arg in arg:
                        match keyword_arg:
                            case ("keyword", var_expr, val_expr):
                                # var_expr könnte ('var', 'name') oder direkt 'name' sein
                                if isinstance(var_expr, tuple) and var_expr[0] == "var":
                                    key = var_expr[1]
                                else:
                                    key = var_expr
                                value = eval_func(val_expr, env)
                                keyword_args[key] = value
                else:
                    # Positionsargument
                    pos_args.append(eval_func(arg, env))
        case _:
            # Einzelnes Argument
            if args_expr is not None:
                pos_args.append(eval_func(args_expr, env))

    return pos_args, keyword_args


def call_lambda(lambda_obj, pos_args, keyword_args, eval_func, env):
    """Führt einen Lambda-Ausdruck aus oder erstellt Partial Application"""
    bound_args = {}
    varargs_values = []

    # Zuerst Keyword-Argumente binden
    for name, value in keyword_args.items():
        if name in lambda_obj.params:
            bound_args[name] = value
        elif lambda_obj.varargs:
            # Keyword-Argumente für varargs werden ignoriert
            pass
        else:
            raise TypeError(f"Unexpected keyword argument '{name}'")

    # Dann Positionsargumente
    unbound_params = [p for p in lambda_obj.params if p not in bound_args]

    for i, arg in enumerate(pos_args):
        if i < len(unbound_params):
            bound_args[unbound_params[i]] = arg
        elif lambda_obj.varargs:
            varargs_values.append(arg)
        else:
            pass
            # raise TypeError("Too many positional arguments")

    # Prüfen ob Parameter fehlen und Defaults verwenden
    missing_params = []
    for param in lambda_obj.params:
        if param not in bound_args:
            if param in lambda_obj.defaults:
                bound_args[param] = lambda_obj.defaults[param]
            else:
                missing_params.append(param)

    if missing_params:
        # Partial Application erstellen
        return PartialApplication(lambda_obj, bound_args)

    # Lambda ausführen
    return execute_lambda(lambda_obj, bound_args, varargs_values, eval_func, env)


def call_partial_application(partial_app, pos_args, keyword_args, eval_func, env):
    """Führt eine Partial Application weiter aus"""
    original = partial_app.original_lambda
    # Kopie der bereits gebundenen Argumente erstellen
    bound_args = partial_app.bound_args.copy()

    # Neue Keyword-Argumente zu bereits gebundenen hinzufügen
    for name, value in keyword_args.items():
        if name in original.params:
            bound_args[name] = value
        elif original.varargs:
            pass  # Ignorieren für varargs
        else:
            raise TypeError(f"Unexpected keyword argument '{name}'")

    # Prüfen welche Parameter noch ungebunden sind
    unbound_params = [p for p in original.params if p not in bound_args]

    # Positionsargumente an ungebundene Parameter binden
    varargs_values = []
    for i, arg in enumerate(pos_args):
        if i < len(unbound_params):
            bound_args[unbound_params[i]] = arg
        elif original.varargs:
            varargs_values.append(arg)

    # Prüfen ob noch Parameter fehlen (die keine defaults haben)
    still_missing = []
    for param in original.params:
        if param not in bound_args and param not in original.defaults:
            still_missing.append(param)

    if still_missing:
        # Immer noch nicht vollständig - weitere Partial Application
        return PartialApplication(original, bound_args)
    else:
        # Defaults für fehlende Parameter setzen
        for param in original.params:
            if param not in bound_args:
                bound_args[param] = original.defaults[param]

        # Vollständig - Lambda ausführen
        return execute_lambda(original, bound_args, varargs_values, eval_func, env)


def execute_lambda(lambda_obj, bound_args, varargs_values, eval_func, env):
    """Führt den Lambda-Body aus"""
    # Neues Environment für die Ausführung
    local_env = Environment(parent=lambda_obj.closure_env)

    # Parameter binden
    for name, value in bound_args.items():
        local_env.put([name])
        local_env[name] = value

    # Varargs binden
    if lambda_obj.varargs:
        local_env.put([lambda_obj.varargs])
        local_env[lambda_obj.varargs] = varargs_values

    # Body ausführen
    return eval_func(lambda_obj.body, local_env)


# def call_partial_application_alt(partial_app, pos_args, keyword_args, eval_func, env):
#     """Führt eine Partial Application weiter aus"""
#     original = partial_app.original_lambda
#     bound_args = partial_app.bound_args.copy()
#
#     # Neue Keyword-Argumente zu bereits gebundenen hinzufügen
#     bound_args.update(keyword_args)
#
#     # Prüfen welche Parameter noch ungebunden sind
#     unbound_params = [p for p in original.params if p not in bound_args]
#
#     if len(pos_args) > len(unbound_params):
#         # Zu viele Positionsargumente - an varargs weitergeben wenn vorhanden
#         if not original.varargs:
#             raise TypeError("Too many positional arguments")
#
#     # Positionsargumente binden
#     varargs_values = []
#     for i, arg in enumerate(pos_args):
#         if i < len(unbound_params):
#             bound_args[unbound_params[i]] = arg
#         elif original.varargs:
#             varargs_values.append(arg)
#
#     # Prüfen ob noch Parameter fehlen (die keine defaults haben)
#     still_missing = []
#     for param in original.params:
#         if param not in bound_args and param not in original.defaults:
#             still_missing.append(param)
#
#     if still_missing:
#         # Immer noch nicht vollständig - weitere Partial Application
#         return PartialApplication(original, bound_args)
#     else:
#         # Defaults für fehlende Parameter setzen
#         for param in original.params:
#             if param not in bound_args:
#                 bound_args[param] = original.defaults[param]
#
#         # Vollständig - Lambda ausführen
#         return execute_lambda(original, bound_args, varargs_values, eval_func, env)
