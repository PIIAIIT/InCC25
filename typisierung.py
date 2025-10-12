from environment import SymbolTable

OPS = {
    "plus": [
        ("i64", "i64", "i64"),
        ("f64", "f64", "f64"),
        ("str", "str", "str"),
        ("c64", "c64", "c64"),
        ("i64", "c64", "c64"),
        ("c64", "i64", "c64"),
    ],
    "minus": [
        ("i64", "i64", "i64"),
        ("f64", "f64", "f64"),
        ("c64", "c64", "c64"),
        ("i64", "c64", "c64"),
        ("c64", "i64", "c64"),
    ],
    "times": [
        ("i64", "i64", "i64"),
        ("f64", "f64", "f64"),
        ("c64", "c64", "c64"),
        ("i64", "c64", "c64"),
        ("c64", "i64", "c64"),
    ],
    "divide": [
        ("i64", "i64", "f64"),
        ("f64", "f64", "f64"),
        ("c64", "c64", "c64"),
        ("i64", "c64", "c64"),
        ("c64", "i64", "c64"),
    ],
    "divide_ceil": [
        ("i64", "i64", "i64"),
        ("f64", "f64", "f64"),
        ("c64", "c64", "c64"),
        ("i64", "c64", "c64"),
        ("c64", "i64", "c64"),
    ],
    "divide_floor": [
        ("i64", "i64", "i64"),
        ("f64", "f64", "f64"),
        ("c64", "c64", "c64"),
        ("i64", "c64", "c64"),
        ("c64", "i64", "c64"),
    ],
    "mod": [("i64", "i64", "i64"), ("f64", "f64", "f64")],
    "power": [("i64", "i64", "i64"), ("f64", "f64", "f64"), ("c64", "c64", "c64")],
    "exp": [("i64", "i64", "i64"), ("f64", "f64", "f64"), ("c64", "c64", "c64")],
    "and": [("i64", "i64", "i64")],
    "or": [("i64", "i64", "i64")],
    "equals": [
        ("i64", "i64", "i64"),
        ("f64", "f64", "i64"),
        ("str", "str", "i64"),
        ("c64", "c64", "i64"),
    ],
    "unquals": [
        ("i64", "i64", "i64"),
        ("f64", "f64", "i64"),
        ("str", "str", "i64"),
        ("c64", "c64", "i64"),
    ],
    "smaller_than": [
        ("i64", "i64", "i64"),
        ("f64", "f64", "i64"),
        ("str", "str", "i64"),
        ("c64", "c64", "i64"),
    ],
    "smaller_equals": [
        ("i64", "i64", "i64"),
        ("f64", "f64", "i64"),
        ("str", "str", "i64"),
        ("c64", "c64", "i64"),
    ],
    "greater_than": [
        ("i64", "i64", "i64"),
        ("f64", "f64", "i64"),
        ("str", "str", "i64"),
        ("c64", "c64", "i64"),
    ],
    "greater_equals": [
        ("i64", "i64", "i64"),
        ("f64", "f64", "i64"),
        ("str", "str", "i64"),
        ("c64", "c64", "i64"),
    ],
    "not": [("i64", "i64")],
    "uminus": [("i64", "i64"), ("f64", "f64"), ("c64", "c64")],
    "uplus": [("i64", "i64"), ("f64", "f64"), ("c64", "c64")],
}


def typecheck(node, gamma: SymbolTable, debug=True) -> str | None | tuple:
    match node:
        case ("num", _):
            return "i64"
        case ("float", _):
            return "f64"
        case ("str", _):
            return "str"
        case ("complex", _):
            return "c64"
        case ("var", name):
            if name not in gamma:
                raise NameError(f"Undefined variable '{name}'")
            return gamma[name].ty

        case ("binop", op, expr1, expr2):
            t1 = typecheck(expr1, gamma)
            t2 = typecheck(expr2, gamma)
            for a, b, res in OPS[op]:
                if t1 == a and t2 == b:
                    return res
            raise TypeError(f"Unsupported operand types for {op}: '{t1}' and '{t2}'")

        case ("comparison", _, x, y):
            t1 = typecheck(x, gamma)
            t2 = typecheck(y, gamma)
            if t1 != t2:
                raise TypeError(
                    f"Comparison operands must have the same type, got '{t1}' and '{t2}'"
                )
            return "i64"

        case ("assign", None, var_name, ty_var, val):
            if var_name in gamma:
                raise NameError(f"Variable '{var_name}' already defined")
            gamma.put(var_name)
            ty_rhs = typecheck(val, gamma)
            if ty_var is not None:
                if ty_var != ty_rhs:
                    raise TypeError(
                        f"Type mismatch in assignment to '{var_name}': '{ty_var}' and '{ty_rhs}'"
                    )
                gamma[var_name].ty = ty_var
            else:
                gamma[var_name].ty = ty_rhs
            return gamma[var_name].ty

        case ("assign", op, var_name, expr):
            if var_name not in gamma:
                gamma.put(var_name)
                gamma[var_name].ty = None
            ty_lhs = gamma[var_name].ty
            ty_rhs = typecheck(expr, gamma)
            if op is None:
                gamma[var_name].ty = ty_rhs
                return ty_rhs
            for a, b, res in OPS[op]:
                if ty_lhs == a and ty_rhs == b:
                    gamma[var_name].ty = res
                    return res
            raise TypeError(
                f"Unsupported operand types for {op} assignment to '{var_name}': '{ty_lhs}' and '{ty_rhs}'"
            )

        case ("undef", ("var", var)):
            if var not in gamma:
                raise NameError(f"Undefined variable '{var}'")
            gamma[var].ty = None
            return None

        case ("unary", op, expr):
            t = typecheck(expr, gamma)
            for a, res in OPS[op]:
                if t == a:
                    return res
            raise TypeError(f"Unsupported operand type for {op}: '{t}'")

        case ("seq", body):
            for expr in body[:-1]:
                typecheck(expr, gamma)
            return typecheck(body[-1], gamma)

        case ("if", condition, then_body, else_body):
            ty_cond = typecheck(condition, gamma)
            if ty_cond != "i64":
                raise TypeError(f"Condition must be of type 'i64', got '{ty_cond}'")
            ty_then = typecheck(then_body, gamma)

            for else_i in else_body:
                match else_i:
                    case ("else", else_body):
                        if ty_then != typecheck(else_body, gamma):
                            raise TypeError(
                                f"Type mismatch in if-else branches: '{ty_then}' and '{typecheck(else_body, gamma)}'"
                            )
                    case (else_cond, else_body):
                        ty_else_cond = typecheck(else_cond, gamma)
                        if ty_else_cond != "i64":
                            raise TypeError(
                                f"Else-if condition must be of type 'i64', got '{ty_else_cond}'"
                            )
                        if ty_then != typecheck(else_body, gamma):
                            raise TypeError(
                                f"Type mismatch in if-else branches: '{ty_then}' and '{typecheck(else_body, gamma)}'"
                            )
            return ty_then

        case ("while", condition, body):
            t_cond = typecheck(condition, gamma)
            if t_cond != "i64":
                raise TypeError(f"Condition must be of type 'i64', got '{t_cond}'")
            return typecheck(body, gamma)

        case ("loop", counter, interval, body):
            t_interval = typecheck(interval, gamma)
            if t_interval not in ("interval",):
                raise TypeError(
                    f"Loop interval must be of type 'interval', got '{t_interval}'"
                )
            gamma.put(counter)
            gamma[counter].ty = "int"
            return typecheck(body, gamma)

        case ("interval", left_interval, expr1, expr2, right_interval):
            t1 = typecheck(expr1, gamma)
            t2 = typecheck(expr2, gamma)
            if t1 != "i64" or t2 != "i64":
                raise TypeError(
                    f"Interval bounds must be of type 'i64', got '{t1}' and '{t2}'"
                )
            return "interval"

        case ("lambda", parameter, body):
            parmam_type = []
            local_gamma = SymbolTable(gamma)
            for param_group in parameter:
                match param_group:
                    case ("pos", ty_var, name):
                        if name in local_gamma:
                            raise NameError(f"Parameter name '{name}' already defined")
                        local_gamma.put(name)
                        local_gamma[name].ty = ty_var
                        parmam_type.append(local_gamma[name].ty)
                    case ("keyword", ty_var, name, value):
                        if name in local_gamma:
                            raise NameError(f"Parameter name '{name}' already defined")
                        local_gamma.put(name)
                        local_gamma[name].ty = ty_var
                        if typecheck(value, local_gamma) != ty_var:
                            raise TypeError(
                                f"Default value type mismatch for parameter '{name}': expected '{ty_var}', got '{typecheck(value, local_gamma)}'"
                            )
                        parmam_type.append(local_gamma[name].ty)
                    case ("infty", ty_var, name):
                        if name in local_gamma:
                            raise NameError(f"Parameter name '{name}' already defined")
                        local_gamma.put(name)
                        local_gamma[name].ty = ty_var
                        parmam_type.append(local_gamma[name].ty)
            return (
                "->",
                "(" + ", ".join(parmam_type) + ")",
                typecheck(body, local_gamma),
            )

        case ("call", func, args_expr):
            func_type = typecheck(func, gamma)
            if not isinstance(func_type, tuple) or func_type[0] != "->":
                raise TypeError(f"Trying to call a non-function type '{func_type}'")
            args_types = []
            for param_group in args_expr:
                match param_group:
                    case ("pos", name):
                        args_types.append(typecheck(name, gamma))
                    case ("keyword", name, value):
                        args_types.append(typecheck(value, gamma))
            param_types, return_type = func_type[1], func_type[2]
            param_types = (
                param_types[1:-1].split(",")
                if len(param_types) > 2
                else [param_types[1:-1]]
            )
            for parm, args in zip(param_types, args_types):
                if parm.strip() == "?":
                    continue
                if parm.strip() != args:
                    raise TypeError(
                        f"Function argument type mismatch: expected '{parm.strip()}', got '{args}'"
                    )
            # Unterversorgung
            if len(param_types) > len(args_types):
                return (
                    "->",
                    "(" + ",".join(param_types[len(args_types) :]) + ")",
                    return_type,
                )
            # Überversorgung
            if len(param_types) < len(args_types):
                raise TypeError(
                    f"Too many arguments provided: expected {len(param_types)}, got {len(args_types)}"
                )
            return return_type

        case ("let", assignments, body):
            local_gamma = SymbolTable(gamma)
            print("LET", assignments) if debug else None

            for *_, var_name, expr in assignments:
                local_gamma.put(var_name)
                local_gamma[var_name].ty = typecheck(expr, gamma)
            print("LET BODY", body) if debug else None
            return typecheck(body, local_gamma)

        case ("array", list_elements):
            elem_types = [typecheck(elem, gamma) for elem in list_elements]
            if not elem_types:
                return "[]unknown"
            first_type = elem_types[0]
            if any(t != first_type for t in elem_types):
                raise TypeError(
                    f"Array elements must have the same type, got {elem_types}"
                )
            return f"[]{first_type}"

        case ("array_access", array_ptr, index):
            t_array = typecheck(array_ptr, gamma)
            t_index = typecheck(index, gamma)
            assert isinstance(t_array, str)
            if not t_array.startswith("[]"):
                raise TypeError(f"Trying to index a non-array type '{t_array}'")
            if t_index != "i64":
                raise TypeError(f"Array index must be of type 'i64', got '{t_index}'")
            return t_array[2:]

        case ("list", list_elements):
            elem_types = [typecheck(elem, gamma) for elem in list_elements]
            if not elem_types:
                return "list[unknown]"
            first_type = elem_types[0]
            if any(t != first_type for t in elem_types):
                raise TypeError(
                    f"List elements must have the same type, got {elem_types}"
                )
            return f"list[{first_type}]"

        case ("cons", expr1, expr2):
            t1 = typecheck(expr1, gamma)
            t2 = typecheck(expr2, gamma)
            assert isinstance(t2, str)
            if not t2.startswith("list[") or not t2.endswith("]"):
                raise TypeError(f"Trying to cons to a non-list type '{t2}'")
            elem_type = t2[5:-1]
            if t1 != elem_type:
                raise TypeError(
                    f"Cons element type mismatch: expected '{elem_type}', got '{t1}'"
                )
            return t2

        case "leere":
            return "[]unknown"

        # case ("import", [path]):
        #     return "i64"

        # case ("match", expr, cases):
        #     t_expr = typecheck(expr, gamma)
        #     case_types = []
        #     for pattern, body in cases:
        #         if pattern != "_":
        #             t_pattern = typecheck(pattern, gamma)
        #             if t_pattern != t_expr:
        #                 raise TypeError(
        #                     f"Match pattern type '{t_pattern}' does not match expression type '{t_expr}'"
        #                 )
        #         t_body = typecheck(body, gamma)
        #         case_types.append(t_body)
        #     first_type = case_types[0]
        #     if any(t != first_type for t in case_types):
        #         raise TypeError(
        #             f"Match case bodies must have the same type, got {case_types}"
        #         )
        #     return first_type
        #
        # case ("struct", attributes):
        #     attr_types = {}
        #     for _, _, name, _, expr in attributes:
        #         attr_types[name] = typecheck(expr, gamma)
        #     return f"struct{{{', '.join(f'{k}: {v}' for k, v in attr_types.items())}}}"
        # case ("access_struct", struct, ("var", name)):
        #     t_struct = typecheck(struct, gamma)
        #     assert isinstance(t_struct, str)
        #     if not t_struct.startswith("struct{") or not t_struct.endswith("}"):
        #         raise TypeError(
        #             f"Trying to access attribute of a non-struct type '{t_struct}'"
        #         )
        #     attr_str = t_struct[7:-1]
        #     attr_dict = {}
        #     for attr in attr_str.split(","):
        #         attr_name, attr_type = attr.split(":")
        #         attr_dict[attr_name.strip()] = attr_type.strip()
        #     if name not in attr_dict:
        #         raise AttributeError(f"Struct has no attribute '{name}'")
        #     return attr_dict[name]

        case _:
            raise TypeError(f"Unknown expression type: {node}")
