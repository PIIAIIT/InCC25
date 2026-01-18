from parser import Node

DEBUG = False
OPS = {}


def add(op, *sig):
    if op not in OPS:
        OPS[op] = {tuple(sig[:-1]): sig[-1]}
    elif list(sig[:-1]) not in [list(s[:-1]) for s in OPS[op]]:
        OPS[op][tuple(sig[:-1])] = sig[-1]


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


def mksymtabs(node, gamma):
    node.sym = gamma
    print(f"{str(node)[:50]:50}, {str(node.sym)[:95]:95}") if DEBUG else None
    match node.ast:
        case "seq" | "array", exprs:
            for expr in exprs:
                mksymtabs(expr, gamma)
        case "comparison", _, x, y:
            exprs, tmp = [x], y
            while tmp[0] == "comparison":
                exprs.append(tmp[2])
                tmp = tmp[3]
            exprs.append(tmp)
            for expr in exprs:
                mksymtabs(expr, gamma)
        case "if", condition, then_body, else_body:
            mksymtabs(condition, gamma)
            mksymtabs(then_body, gamma)
            for else_cond, else_body in else_body:
                if else_cond != "else":
                    mksymtabs(else_cond, gamma)
                mksymtabs(else_body, gamma)
        case "call", func, args_expr:
            mksymtabs(func, gamma)
            for param_group in args_expr:
                match param_group:
                    case ("pos", name):
                        mksymtabs(name, gamma)
                    case ("keyword", name, value):
                        mksymtabs(value, gamma)
        case "program", body:
            mksymtabs(body, gamma)
        case "assign", _, var_name, val:
            if var_name not in gamma:
                raise NameError(f"Undefined variable '{var_name}'")
            mksymtabs(val, gamma)
        case "var", name:
            if name not in gamma:
                raise NameError(f"Undefined variable '{name}'")
        case "lambda", parameter, body, _:
            names = [name for _, _, name, *_ in parameter]
            local_gamma = gamma.cpy(names)
            mksymtabs(body, local_gamma)
        case "letrec", assignments, body:
            names = [name for _, _, name, _ in assignments]
            local_gamma = gamma.cpy(names)
            for assgn in assignments:
                mksymtabs(assgn, local_gamma)
            mksymtabs(body, local_gamma)
        case "loop", counter, interval, body:
            mksymtabs(interval, gamma)
            local_gamma = gamma.cpy(counter)
            mksymtabs(body, local_gamma)
        case (
            "num"
            | "float"
            | "str"
            | "complex"
            | "binop"
            | "unary"
            | "interval"
            | "list"
            | "cons"
            | "leere"
            | "match"
            | "undef"
            | "import"
            | "struct"
            | "access_struct"
            | "while"
            | "array_access",
            *_,
        ):
            for child in node.children():
                if isinstance(child, Node):
                    mksymtabs(child, gamma)
        case _:
            raise NotImplementedError(f"Unknown AST node: {node}")


def typecheck(node):
    node.ty = _typecheck(node)
    return node.ty


def _typecheck(node, debug=DEBUG or False):
    match node.ast:
        case ("num", _):
            return "i64"
        case ("float", _):
            return "f64"
        case ("str", _):
            return "str"
        case ("complex", _):
            return "c64"
        case ("var", name):
            if name not in node.sym:
                raise NameError(f"Undefined variable '{name}'")
            return node.sym[name].ty
        case ("binop", op, expr1, expr2):
            t1 = typecheck(expr1)
            t2 = typecheck(expr2)
            if OPS[op].get((t1, t2)) is None:
                raise TypeError(
                    f"Operator '{op}' not defined for types '{t1}' and '{t2}'"
                )
            return OPS[op][(t1, t2)]

        case ("comparison", _, x, y):
            t1 = typecheck(x)
            t2 = typecheck(y)
            if t1 != t2:
                raise TypeError(
                    f"Comparison operands must have the same type, got '{t1}' and '{t2}'"
                )
            return "i64"

        case ("assign", ty_var, name, val):
            if name not in node.sym:
                raise NameError(f"Undefined variable '{name}'")
            rhs_ty = typecheck(val)
            if ty_var is None:
                tty_var = node.sym[name].ty
                if tty_var is None:
                    node.sym[name].ty = rhs_ty
                    return rhs_ty
                else:
                    ty_var = tty_var
            if ty_var != rhs_ty:
                raise TypeError(
                    f"Type mismatch in assignment to '{name}': '{ty_var}' and '{rhs_ty}'"
                )
            node.sym[name].ty = ty_var
            return ty_var

        case ("undef", ("var", var)):
            if var not in node.sym:
                raise NameError(f"Undefined variable '{var}'")
            node.sym[var].ty = None
            return None

        case ("unary", op, expr):
            t = typecheck(expr)
            if OPS[op].get((t,)) is None:
                raise TypeError(f"Operator '{op}' not defined for type '{t}'")
            return OPS[op][(t,)]

        case ("seq", body):
            for expr in body[:-1]:
                typecheck(expr)
            return typecheck(body[-1])

        case ("if", condition, then_body, else_body):
            ty_cond = typecheck(condition)
            if ty_cond != "i64":
                raise TypeError(f"Condition must be of type 'i64', got '{ty_cond}'")
            ty_then = typecheck(then_body)

            for else_cond, else_body in else_body:
                if else_cond == "else":
                    if ty_then != typecheck(else_body):
                        raise TypeError(
                            f"Type mismatch in if-else branches: '{ty_then}' and '{typecheck(else_body)}'"
                        )
                else:  # else_cond is an elif
                    ty_else_cond = typecheck(else_cond)
                    if ty_else_cond != "i64":
                        raise TypeError(
                            f"Else-if condition must be of type 'i64', got '{ty_else_cond}'"
                        )
                    if ty_then != typecheck(else_body):
                        raise TypeError(
                            f"Type mismatch in if-else branches: '{ty_then}' and '{typecheck(else_body)}'"
                        )
            return ty_then

        case ("while", condition, body):
            t_cond = typecheck(condition)
            if t_cond != "i64":
                raise TypeError(f"Condition must be of type 'i64', got '{t_cond}'")
            return typecheck(body)

        case ("loop", counter, interval, body):
            t_interval = typecheck(interval)
            body.sym[counter].ty = "i64"

            for k, v in node.sym.items():
                body.sym[k].ty = v.ty

            if not t_interval.startswith("[]"):
                raise TypeError(
                    f"Loop interval must be of type 'interval', got '{t_interval}'"
                )
            return typecheck(body)

        case ("interval", _, expr1, expr2, _):
            t1 = typecheck(expr1)
            t2 = typecheck(expr2)
            if [t1, t2] != ["i64", "i64"]:
                raise TypeError(
                    f"Interval bounds must be of type 'i64', got '{t1}' and '{t2}'"
                )
            return "[]i64"

        case ("lambda", parameter, body, ret_ty):
            for k, v in node.sym.items():
                body.sym[k].ty = v.ty
            parmam_type = []
            for param_group in parameter:
                match param_group:
                    case ("pos", ty_var, name):
                        parmam_type.append(ty_var)
                        body.sym[name].ty = ty_var
                    case ("keyword", ty_var, name, value):
                        parmam_type.append(ty_var)
                        body.sym[name].ty = ty_var
                    case ("infty", ty_var, name):
                        parmam_type.append(ty_var)
                        body.sym[name].ty = ty_var
            return ("->", tuple(parmam_type), ret_ty)

        case ("call", func, args_expr):
            func_type = typecheck(func)
            if not isinstance(func_type, tuple) or not func_type[0] in {"->"}:
                raise TypeError(f"Trying to call a non-function type '{func_type}'")
            args_types = []
            for param_group in args_expr:
                match param_group:
                    case ("pos", name):
                        args_types.append(typecheck(name))
                    case ("keyword", name, value):
                        args_types.append(typecheck(value))
            param_types, return_type = func_type[1], func_type[2]
            for parm, args in zip(param_types, args_types):
                if parm.strip() != args:
                    raise TypeError(
                        f"Function argument type mismatch: expected '{parm.strip()}', got '{args}'"
                    )
            # Unterversorgung
            if len(param_types) > len(args_types):
                return (
                    "->",
                    param_types[len(args_types) :],
                    return_type,
                )
            else:
                return return_type

        case ("letrec", assignments, body):
            print("LET", assignments) if debug else None

            # node sym to body sym
            for k, v in node.sym.items():
                body.sym[k].ty = v.ty

            for assgn in assignments:
                _, ty, name, _ = assgn
                typecheck(assgn)
                body.sym[name].ty = ty

            for _, ty, name, rhs in assignments:
                rhs_ty = typecheck(rhs)

                if ty != rhs_ty:
                    raise TypeError(
                        f"Type mismatch in letrec assignment to '{name}': '{ty}' and '{rhs_ty}'"
                    )

            print("LET BODY", body) if debug else None
            return typecheck(body)

        case ("array", list_elements):
            elem_types = [typecheck(elem) for elem in list_elements]
            if not elem_types:
                raise TypeError("Cannot infer type of empty array")
            first_type = elem_types[0]
            if any(t != first_type for t in elem_types):
                raise TypeError(
                    f"Array elements must have the same type, got {elem_types}"
                )
            return f"[]{first_type}"

        case ("array_access", array_ptr, index):
            t_array = typecheck(array_ptr)
            t_index = typecheck(index)
            if (
                not t_array.startswith("[]")
                and not t_array.startswith("interval")
                and not t_array.startswith("str")
            ):
                raise TypeError(f"Trying to index a non-array type '{t_array}'")
            if t_index != "i64":
                raise TypeError(f"Array index must be of type 'i64', got '{t_index}'")

            if t_array == "str":
                return "str"
            else:
                return t_array[2:]

        case ("list", list_elements):
            elem_types = [typecheck(elem) for elem in list_elements]
            if not elem_types:
                return "[]unknown"
            first_type = elem_types[0]
            if any(t != first_type for t in elem_types):
                raise TypeError(
                    f"List elements must have the same type, got {elem_types}"
                )
            return f"[]{first_type}"

        case ("cons", expr1, expr2):
            t1 = typecheck(expr1)
            t2 = typecheck(expr2)
            if not t2.startswith("[]"):
                raise TypeError(f"Trying to cons to a non-list type '{t2}'")
            elem_type = t2[2:]
            if t1 != elem_type:
                raise TypeError(
                    f"Cons element type mismatch: expected '{elem_type}', got '{t1}'"
                )
            return t2

        case "leere":
            return "[]unknown"

        case ("import", _):
            return "i64"

        case ("match", expr, cases):
            t_expr = typecheck(expr)
            case_types = []
            for pattern, body in cases:
                if pattern != "_":
                    t_pattern = typecheck(pattern)
                    if t_pattern != t_expr:
                        raise TypeError(
                            f"Match pattern type '{t_pattern}' does not match expression type '{t_expr}'"
                        )
                t_body = typecheck(body)
                case_types.append(t_body)
            first_type = case_types[0]
            if any(t != first_type for t in case_types):
                raise TypeError(
                    f"Match case bodies must have the same type, got {case_types}"
                )
            return first_type

        case ("struct", attributes):
            attr_types = {}
            for _, _, name, _, expr in attributes:
                attr_types[name] = typecheck(expr)
            return f"struct{{{', '.join(f'{k}: {v}' for k, v in attr_types.items())}}}"
        case ("access_struct", struct, ("var", name)):
            t_struct = typecheck(struct)
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
            return attr_dict[name]

        case "program", expr:
            return typecheck(expr)
        case _:
            raise TypeError(f"Unknown expression type: {node}")
