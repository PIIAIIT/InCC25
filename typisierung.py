from environment import SymbolTable

DEBUG = False
OPS = {}


def add(op, *sig):
    if op not in OPS:
        OPS[op] = [sig]
    elif list(sig[:-1]) not in [list(s[:-1]) for s in OPS[op]]:
        OPS[op].append(sig)


def add_all(ops, *sig):
    for op in ops:
        add(op, *sig)


T = dict(i="i64", f="f64", c="c64")
add_all(["plus", "minus", "times", "divide_ceil", "divide_floor"], *(3 * (T["i"],)))
add_all(["plus", "minus", "times", "divide"], *(3 * (T["f"],)))
add_all(["plus", "minus", "times", "divide"], *(3 * (T["c"],)))
add("divide", T["i"], T["i"], T["f"])
add_all(["and", "or", "xor"], *(3 * (T["i"],)))
add("not", *(2 * (T["i"],)))
add_all(["uminus", "uplus"], *(2 * (T["i"],)))
add_all(["uminus", "uplus"], *(2 * (T["f"],)))
add_all(["uminus", "uplus"], *(2 * (T["c"],)))
comp = ["equals", "unequals", "less", "less_equals", "greater", "greater_equals"]
add_all(comp, *(3 * (T["i"],)))
add_all(comp, *(3 * (T["f"],)))
add_all(comp, *(3 * (T["c"],)))
add_all(["mod", "power", "exp"], *(3 * (T["i"],)))
add_all(["mod", "power", "exp"], *(3 * (T["f"],)))
add_all(["power", "exp"], *(3 * (T["c"],)))
print("OPS:", OPS) if DEBUG else None


def typecheck(node, gamma):
    print(node)
    node.sym = gamma.copy()
    return _typecheck(node, gamma)


def _typecheck(node, gamma, debug=DEBUG or False):
    match node.ast:
        case ("num", _):
            node.ty = "i64"
        case ("float", _):
            node.ty = "f64"
        case ("str", _):
            node.ty = "str"
        case ("complex", _):
            node.ty = "c64"
        case ("var", name):
            if name not in gamma:
                raise NameError(f"Undefined variable '{name}'")
            node.ty = gamma[name].ty

        case ("binop", op, expr1, expr2):
            t1 = typecheck(expr1, gamma).ty
            t2 = typecheck(expr2, gamma).ty
            for a, b, res in OPS[op]:
                if t1 == a and t2 == b:
                    node.ty = res
                    return node

        case ("comparison", _, x, y):
            t1 = typecheck(x, gamma).ty
            t2 = typecheck(y, gamma).ty
            if t1 != t2:
                raise TypeError(
                    f"Comparison operands must have the same type, got '{t1}' and '{t2}'"
                )
            node.ty = "i64"

        case ("assign", ty_var, var_name, val):
            if var_name not in gamma:
                gamma.put(var_name)
                gamma[var_name].ty = ty_var
            ty_lhs = gamma[var_name].ty
            ty_rhs = typecheck(val, gamma).ty
            if ty_var is not None and ty_var != ty_lhs:
                raise TypeError(
                    f"Type annotation mismatch for variable '{var_name}': '{ty_var}' and '{ty_lhs}'"
                )
            elif ty_lhs != ty_rhs and ty_lhs is not None:
                raise TypeError(
                    f"Type mismatch in assignment to '{var_name}': '{ty_lhs}' and '{ty_rhs}'"
                )
            if ty_lhs is None:
                ty_lhs = gamma[var_name].ty = ty_rhs
            node.ty = ty_lhs
            node.sym = gamma

        case ("undef", ("var", var)):
            if var not in gamma:
                raise NameError(f"Undefined variable '{var}'")
            gamma[var].ty = None
            node.ty = None

        case ("unary", op, expr):
            t = typecheck(expr, gamma).ty
            for a, res in OPS[op]:
                if t == a:
                    node.ty = res

        case ("seq", body):
            for expr in body[:-1]:
                typecheck(expr, gamma).ty
            node.ty = typecheck(body[-1], gamma).ty

        case ("if", condition, then_body, else_body):
            ty_cond = typecheck(condition, gamma).ty
            if ty_cond != "i64":
                raise TypeError(f"Condition must be of type 'i64', got '{ty_cond}'")
            ty_then = typecheck(then_body, gamma).ty

            for else_cond, else_body in else_body:
                if else_cond == "else":
                    if ty_then != typecheck(else_body, gamma).ty:
                        raise TypeError(
                            f"Type mismatch in if-else branches: '{ty_then}' and '{typecheck(else_body, gamma).ty}'"
                        )
                else:  # else_cond is an elif
                    ty_else_cond = typecheck(else_cond, gamma).ty
                    if ty_else_cond != "i64":
                        raise TypeError(
                            f"Else-if condition must be of type 'i64', got '{ty_else_cond}'"
                        )
                    if ty_then != typecheck(else_body, gamma).ty:
                        raise TypeError(
                            f"Type mismatch in if-else branches: '{ty_then}' and '{typecheck(else_body, gamma).ty}'"
                        )
            node.ty = ty_then

        case ("while", condition, body):
            t_cond = typecheck(condition, gamma).ty
            if t_cond != "i64":
                raise TypeError(f"Condition must be of type 'i64', got '{t_cond}'")
            node.ty = typecheck(body, gamma).ty

        case ("loop", counter, interval, body):
            t_interval = typecheck(interval, gamma).ty
            if not t_interval.startswith("[]"):
                raise TypeError(
                    f"Loop interval must be of type 'interval', got '{t_interval}'"
                )
            gamma.put(counter)
            gamma[counter].ty = "i64"
            node.ty = typecheck(body, gamma).ty

        case ("interval", _, expr1, expr2, _):
            t1 = typecheck(expr1, gamma).ty
            t2 = typecheck(expr2, gamma).ty
            if [t1, t2] != ["i64", "i64"]:
                raise TypeError(
                    f"Interval bounds must be of type 'i64', got '{t1}' and '{t2}'"
                )
            node.ty = "[]i64"

        case ("lambda", parameter, body, ret_ty):
            parmam_type = []
            local_gamma = SymbolTable(gamma)
            for param_group in parameter:
                match param_group:
                    case ("pos", ty_var, name):
                        local_gamma.put(name)
                        local_gamma[name].ty = ty_var
                        parmam_type.append(local_gamma[name].ty)
                    case ("keyword", ty_var, name, value):
                        local_gamma.put(name)
                        local_gamma[name].ty = ty_var
                        if typecheck(value, local_gamma).ty != ty_var:
                            raise TypeError(
                                f"Default value type mismatch for parameter '{name}': expected '{ty_var}', got '{typecheck(value, local_gamma).ty}'"
                            )
                        parmam_type.append(local_gamma[name].ty)
                    case ("infty", ty_var, name):
                        local_gamma.put(name)
                        local_gamma[name].ty = ty_var
                        parmam_type.append(local_gamma[name].ty)
            if ret_ty != typecheck(body, local_gamma).ty:
                raise TypeError(
                    f"Lambda return type mismatch: expected '{ret_ty}', got '{typecheck(body, local_gamma).ty}'"
                )
            node.ty = ("->", parmam_type, ret_ty)
            node.sym = local_gamma

        case ("call", func, args_expr):
            func_type = typecheck(func, gamma).ty
            if not isinstance(func_type, tuple) or not func_type[0] in {"->"}:
                raise TypeError(f"Trying to call a non-function type '{func_type}'")
            args_types = []
            for param_group in args_expr:
                match param_group:
                    case ("pos", name):
                        args_types.append(typecheck(name, gamma).ty)
                    case ("keyword", name, value):
                        args_types.append(typecheck(value, gamma).ty)
            param_types, return_type = func_type[1], func_type[2]
            for parm, args in zip(param_types, args_types):
                if parm.strip() != args:
                    raise TypeError(
                        f"Function argument type mismatch: expected '{parm.strip()}', got '{args}'"
                    )
            # Unterversorgung
            if len(param_types) > len(args_types):
                node.ty = (
                    "->",
                    param_types[len(args_types) :],
                    return_type,
                )
            else:
                node.ty = return_type

        case ("letrec", assignments, body):
            print("LET", assignments) if debug else None
            local_gamma = SymbolTable(gamma)

            for _, ty, var_name, val in assignments:
                local_gamma.put(var_name)
                local_gamma[var_name].ty = ty

            for _, ty, var_name, val in assignments:
                rhs_ty = typecheck(val, local_gamma).ty

                if ty != rhs_ty and ty is not None:
                    raise TypeError(
                        f"Type mismatch in let binding for '{var_name}': '{ty}' and '{local_gamma[var_name].ty}'"
                    )

            print("LET BODY", body) if debug else None
            node.ty = typecheck(body, local_gamma).ty
            node.sym = local_gamma

        case ("array", list_elements):
            elem_types = [typecheck(elem, gamma).ty for elem in list_elements]
            if not elem_types:
                node.ty = "[]unknown"
                return node
            first_type = elem_types[0]
            if any(t != first_type for t in elem_types):
                raise TypeError(
                    f"Array elements must have the same type, got {elem_types}"
                )
            node.ty = f"[]{first_type}"

        case ("array_access", array_ptr, index):
            t_array = typecheck(array_ptr, gamma).ty
            t_index = typecheck(index, gamma).ty
            if not t_array.startswith("[]"):
                raise TypeError(f"Trying to index a non-array type '{t_array}'")
            if t_index != "i64":
                raise TypeError(f"Array index must be of type 'i64', got '{t_index}'")
            node.ty = t_array[2:]

        case ("list", list_elements):
            elem_types = [typecheck(elem, gamma).ty for elem in list_elements]
            if not elem_types:
                node.ty = "[]unknown"
            first_type = elem_types[0]
            if any(t != first_type for t in elem_types):
                raise TypeError(
                    f"List elements must have the same type, got {elem_types}"
                )
            node.ty = f"[]{first_type}"

        case ("cons", expr1, expr2):
            t1 = typecheck(expr1, gamma).ty
            t2 = typecheck(expr2, gamma).ty
            if not t2.startswith("[]"):
                raise TypeError(f"Trying to cons to a non-list type '{t2}'")
            elem_type = t2[2:]
            if t1 != elem_type:
                raise TypeError(
                    f"Cons element type mismatch: expected '{elem_type}', got '{t1}'"
                )
            node.ty = t2

        case "leere":
            node.ty = "[]unknown"

        case ("import", _):
            node.ty = "i64"

        case ("match", expr, cases):
            t_expr = typecheck(expr, gamma).ty
            case_types = []
            for pattern, body in cases:
                if pattern != "_":
                    t_pattern = typecheck(pattern, gamma).ty
                    if t_pattern != t_expr:
                        raise TypeError(
                            f"Match pattern type '{t_pattern}' does not match expression type '{t_expr}'"
                        )
                t_body = typecheck(body, gamma).ty
                case_types.append(t_body)
            first_type = case_types[0]
            if any(t != first_type for t in case_types):
                raise TypeError(
                    f"Match case bodies must have the same type, got {case_types}"
                )
            node.ty = first_type

        case ("struct", attributes):
            attr_types = {}
            for _, _, name, _, expr in attributes:
                attr_types[name] = typecheck(expr, gamma).ty
            node.ty = (
                f"struct{{{', '.join(f'{k}: {v}' for k, v in attr_types.items())}}}"
            )
        case ("access_struct", struct, ("var", name)):
            t_struct = typecheck(struct, gamma).ty
            assert isinstance(t_struct, str)
            if not t_struct.startswith("struct{") or not t_struct.endswith("}"):
                raise TypeError(
                    f"Trying to access attribute of a non-struct type '{t_struct}'"
                )
            attr_str = t_struct[7:-1]
            attr_dict = {}
            for attr in attr_str.split(","):
                attr_name, attr_type = attr.split(":")
                attr_dict[attr_name.strip()] = attr_type.strip()
            if name not in attr_dict:
                raise AttributeError(f"Struct has no attribute '{name}'")
            node.ty = attr_dict[name]

        case "program", expr:
            node.ty = typecheck(expr, gamma).ty
        case _:
            raise TypeError(f"Unknown expression type: {node}")
    return node
