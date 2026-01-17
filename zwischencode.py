from optimierung import CFGraph, liveness
from parser import Node
from typing import Any
from utils import gen_label, gen_reg
from ice2_ws25.ice_machine import tuple_to_infix

OPS = {
    "plus": "+",
    "minus": "-",
    "times": "*",
    "divide": "|",
    "power": "**",
    "mod": "%",
    "divide_ceil": "/",
    "divide_floor": "\\",
    "equals": "==",
    "greater_than": ">",
    "smaller_than": "<",
    "greater_equals": ">=",
    "smaller_equals": "<=",
    "unequals": "!=",
    "and": "and",
    "or": "or",
    "not": "not",
    "xor": "xor",
    "uminus": "u-",
    "uplus": "u+",
    "imag": "i+",
}


LABELS = {
    "if": gen_label("if", "else", "end_if"),
    "elif": gen_label("elif", "elif_body"),
    "while": gen_label("while", "end_while"),
    "seq": gen_label("seq"),
    "loop": gen_label("loop", "end_loop"),
    "let": gen_label("letrec"),
    "lambda": gen_label("lambda"),
    "call": gen_label("call"),
}


def iic_gen(node, debug=False):
    lambda_env = dict()
    inter_result = code_c(node, lambda_env, "R0", set(), code_b)
    print("Intermediate Code Generation Complete.") if debug else None

    func_res = [x for sublist in list(lambda_env.values()) for x in sublist]

    inter_result = func_res + inter_result

    cfg = CFGraph(inter_result)
    liveness(cfg)

    return cfg.iir


def code_c(node, lmbd, ret, used, code_x):
    match node.ast:
        case ("program", expr):
            code_c(expr, lmbd, ret, used, code_x)
            node.code = [("label", "main"), *expr.code]

        case "seq", exprs:
            (seq_l,) = next(LABELS["seq"])
            node.code = [("comment", f"seq start {seq_l}")]
            for expr in exprs[:-1]:
                node.code += code_c(expr, lmbd, ret, used, code_x)
            node.code += code_c(exprs[-1], lmbd, ret, used, code_x)
            node.code += [("comment", f"seq end {seq_l}")]

        case (
            "num"
            | "float"
            | "str"
            | "complex"
            | "var"
            | "binop"
            | "comparison"
            | "unary"
            | "assign"
            | "lambda"
            | "array"
            | "call",
            *_,
        ):
            code_x(node, lmbd, ret, used)

        case "array_access", array, index:
            arr_reg, idx_reg = gen_reg(used | {ret}, 2)
            code_c(array, lmbd, arr_reg, used | {ret}, code_v)
            code_c(index, lmbd, idx_reg, used | {ret, arr_reg}, code_b)
            node.code = [
                ("comment", "array access"),
                *array.code,
                ("=[]", array.ty, ret, arr_reg, 0),  # make array code_b
                *index.code,
                (
                    "=[]",
                    array.ty[2:] if array.ty.startswith("[]") else "i64",
                    ret,
                    ret,
                    idx_reg,
                ),  # dereference array
            ]

        case "if", condition, then_body, else_body:
            has_else = bool(else_body and else_body[-1][0] == "else")
            n_elifs = len(else_body) - (1 if has_else else 0)

            if_l, else_l, end_l = next(LABELS["if"])
            elif_cond_l = [next(LABELS["elif"])[0] for _ in range(n_elifs)]
            elif_body_l = [next(LABELS["elif"])[1] for _ in range(n_elifs)]

            code_c(condition, lmbd, ret, used, code_b)
            code_c(then_body, lmbd, ret, used, code_x)

            for i in range(n_elifs):
                cond, body = else_body[i]
                code_c(cond, lmbd, ret, used, code_b)
                code_c(body, lmbd, ret, used, code_x)
            if has_else:
                code_c(else_body[-1][1], lmbd, ret, used, code_x)

            l_elifs = []
            for i in range(n_elifs):
                cond_label, body_label = elif_cond_l[i], elif_body_l[i]
                next_label = (
                    elif_cond_l[i + 1]
                    if i + 1 < n_elifs
                    else (else_l if has_else else end_l)
                )
                cond_node, body_node = else_body[i]
                l_elifs += [
                    ("label", cond_label),
                    *cond_node.code,
                    ("ifgoto", ret, body_label),
                    ("goto", next_label),
                    ("label", body_label),
                    *body_node.code,
                    ("goto", end_l),
                ]
            l_else = (
                [
                    ("label", else_l),
                    *else_body[-1][1].code,
                ]
                if has_else
                else []
            )

            node.code = [
                ("comment", f"condition of {if_l}"),
                *condition.code,
                ("ifgoto", ret, if_l),
                (
                    "goto",
                    elif_cond_l[0] if n_elifs > 0 else (else_l if has_else else end_l),
                ),
                ("label", if_l),
                ("comment", f"then body of {if_l}"),
                *then_body.code,
                ("goto", end_l),
                *l_elifs,
                *l_else,
                ("label", end_l),
            ]

        case "while", cond, body:
            while_l, end_l = next(LABELS["while"])
            (cond_reg,) = gen_reg(used | {ret})

            code_c(cond, lmbd, cond_reg, used | {ret}, code_b)
            code_c(body, lmbd, ret, used, code_x)

            node.code = [
                ("label", while_l),
                *cond.code,
                ("not", cond_reg, cond_reg),
                ("ifgoto", cond_reg, end_l),
                *body.code,
                ("goto", while_l),
                ("label", end_l),
            ]

        case "loop", counter, interval, body:
            loop_l, end_l = next(LABELS["loop"])

            (counter_reg, cond_reg) = gen_reg(used | {ret}, 2)

            code_c(interval, lmbd, counter_reg, used, code_v)
            code_c(body, lmbd, ret, used | {counter_reg}, code_x)

            node.code = [
                ("comment", f"loop start {loop_l}"),
                ("mk[]", "i64", counter_reg, 1),
                *counter.code,
                ("label", loop_l),
                ("<=", cond_reg, counter_reg, 0),
                ("ifgoto", cond_reg, end_l),
                ("-", counter_reg, counter_reg, 1),
                *body.code,
                ("goto", loop_l),
                ("label", end_l),
            ]

        case "interval", _, e1, e2, _:
            (tmp_reg,) = gen_reg(used | {ret})
            code_c(e1, lmbd, tmp_reg, used | {ret}, code_b)
            code_c(e2, lmbd, tmp_reg, used | {ret}, code_b)
            node.code = [
                ("comment", "interval"),
                ("mk[]", "*", ret, 2),
                *e1.code,
                ("[]=", ret, 0, tmp_reg),
                *e2.code,
                ("[]=", ret, 1, tmp_reg),
            ]

        case "letrec", decls, body:
            body.sym.cpy(body.free)
            free_names = set()
            for _, _, name, rhs in decls:
                free_names |= rhs.free
            free_names -= {name for *_, name, _ in decls}

            for i, name in enumerate(sorted(body.free | free_names)):
                body.sym[name].idx = i

            (letrec_l,) = next(LABELS["let"])
            (env_reg,) = gen_reg(used | {ret})

            global_vars = []
            for name in sorted(node.free):
                global_vars += [
                    ("=[]", node.sym[name].ty, ret, "V", node.sym[name].idx)
                ]
                global_vars += [("[]=", env_reg, body.sym[name].idx, ret)]

            hulls = []
            for _, ty, var_name, rhs in decls:
                if var_name not in body.free:
                    continue

                match ty:
                    case ("->", *_):
                        hulls += [("mk[]", "*", ret, 2)]
                    case _:
                        hulls += [("mk[]", ret, 0)]
                hulls += [("[]=", env_reg, body.sym[var_name].idx, ret)]

            declared_vars = []
            for _, ty, name, rhs in decls:
                declared_vars += code_c(rhs, lmbd, ret, used, code_v)

                if name in body.free:
                    declared_vars += [("=[]", ty, env_reg, "V", body.sym[name].idx)]
                    declared_vars += [("rewrite", env_reg, ret)]

            code_c(body, lmbd, ret, used, code_x)

            node.code = [
                ("comment", f"env of {letrec_l}"),
                ("mk[]", "*", env_reg, len(body.free | free_names)),
                ("comment", f"global vars of {letrec_l}"),
                *global_vars,
                ("comment", f"hulls of {letrec_l}"),
                *hulls,
                ("enter", env_reg),
                ("comment", f"declared vars of {letrec_l}"),
                *declared_vars,
                ("comment", f"body of {letrec_l}"),
                *body.code,
                ("leave",),
                ("comment", f"end of {letrec_l}"),
            ]

        case _:
            raise NotImplementedError("code_c not implemented for this AST node")

    return node.code


def code_b(node: Node, lmbd, ret, used) -> Any:
    match node.ast:
        case "program", expr:
            code_c(node, lmbd, ret, used, code_v)
            node.code += [("=", ret, ret)]

        case "num" | "float" | "complex" as lit, value:
            _type = {
                "num": lambda x: int(x),
                "float": lambda x: float(x),
                "complex": lambda x: complex(x),
            }
            node.code = [("=", ret, _type[lit](value))]

        case "str", value:
            inner_str = value[1:-1]  # remove quotes
            node.code = [
                ("mk[]", "t_char", ret, len(inner_str)),
                *[("[]=", ret, i, ord(c)) for i, c in enumerate(inner_str)],
            ]

        case "array", elements:
            elem_ty = "*" if len(elements) == 0 else elements[0].ty
            (elem_reg,) = gen_reg(used | {ret})
            code_list = []
            for i, element in enumerate(elements):
                if elem_ty.startswith("[]"):
                    code_c(element, lmbd, elem_reg, used | {ret}, code_v)
                else:
                    code_c(element, lmbd, elem_reg, used | {ret}, code_b)
                code_list += element.code
                code_list.append(("[]=", ret, i, elem_reg))

            node.code = [
                ("comment", "array creation"),
                ("mk[]", elem_ty, ret, len(elements)),
                *code_list,
            ]

        case "var" | "call" | "assign", *_:
            code_c(node, lmbd, ret, used, code_v)
            node.code += [("get", ret, ret)]

        case "binop", "power", lhs, rhs:
            base_reg, exp_reg, tmp_reg, tmp2_reg = gen_reg(used | {ret}, 4)
            loop_label, end_label = next(gen_label("power_loop", "power_end"))

            code_c(lhs, lmbd, base_reg, used | {ret}, code_b)
            code_c(rhs, lmbd, exp_reg, used | {ret, base_reg}, code_b)

            node.code = [
                *lhs.code,
                *rhs.code,
                ("=", ret, 1),
                ("=", tmp_reg, 0),
                ("label", loop_label),
                (">=", tmp2_reg, tmp_reg, exp_reg),
                ("ifgoto", tmp2_reg, end_label),
                ("*", ret, ret, base_reg),
                ("+", tmp_reg, tmp_reg, 1),
                ("goto", loop_label),
                ("label", end_label),
            ]

        case "binop", op, lhs, rhs:
            x_reg, y_reg = gen_reg(used | {ret}, 2)

            code_c(lhs, lmbd, x_reg, used | {ret}, code_b)
            code_c(rhs, lmbd, y_reg, used | {ret, x_reg}, code_b)

            node.code = lhs.code + rhs.code + [(OPS[op], ret, x_reg, y_reg)]

        case "unary", "imag", lhs:
            code_c(lhs, lmbd, ret, used, code_b)
            node.code = lhs.code

        case "unary", op, expr:
            code_c(expr, lmbd, ret, used, code_b)
            node.code = expr.code + [(OPS[op], ret, ret)]

        case "comparison", f, x, y:
            ops, exprs, tmp = [f], [x], y
            while tmp[0] == "comparison":
                ops.append(tmp[1])
                exprs.append(tmp[2])
                tmp = tmp[3]
            exprs.append(tmp)

            r1, r2 = list(gen_reg(used | {ret}, 2))

            code_c(exprs[0], lmbd, r1, used, code_b)
            code_c(exprs[1], lmbd, r2, used, code_b)

            code = [
                *exprs[0].code,
                *exprs[1].code,
                (OPS[ops[0]], ret, r1, r2),
            ]

            def ch(i):
                return r1 if i % 2 == 0 else r2

            for i in range(1, len(ops)):
                code_c(exprs[i + 1], lmbd, ch(i), used | {ret, ch(i - 1)}, code_b)
                code += exprs[i + 1].code
                code += [
                    (OPS[ops[i]], r1, ch(i - 1), ch(i)),
                    ("and", ret, ret, r1),
                ]
            node.code = code
        case _:
            print("E:", node)
            raise Exception("code_b not implemented for this AST node")


def code_v(node: Node, lmbd, ret, used) -> Any:
    match node.ast:
        case "num" | "float" | "binop" | "unary" | "comparison", *_:
            code_c(node, lmbd, ret, used, code_b)
            node.code += [("mk[]", ret, ret)]

        case "str" | "array", _:
            (tmp_reg,) = gen_reg(used | {ret})
            code_c(node, lmbd, tmp_reg, used | {ret}, code_b)
            node.code += [("mk[]", node.ty, ret, 1), ("[]=", ret, 0, tmp_reg)]

        case "var", name:
            node.code = [
                ("comment", f"var: {name}"),
                ("=[]", node.sym[name].ty, ret, "V", node.sym[name].idx),
            ]

        case "assign", _, name, value:
            code_c(value, lmbd, ret, used, code_v)
            (var_reg,) = gen_reg(used | {ret})
            node.code = value.code + [
                ("comment", f"assign: {name}"),
                ("=[]", node.sym[name].ty, var_reg, "V", node.sym[name].idx),
                ("rewrite", var_reg, ret),
            ]

        case "lambda", params, body, _:
            body.sym.cpy(node.free)
            (lambda_l,) = next(LABELS["lambda"])
            (env_reg,) = gen_reg(used | {ret})

            env = [("mk[]", "*", env_reg, len(node.free))]
            for i, name in enumerate(node.free):
                body.sym[name].idx = i
                env += [("=[]", node.sym[name].ty, ret, "V", node.sym[name].idx)]
                env += [("[]=", env_reg, body.sym[name].idx, ret)]

            for i, (*_, name) in enumerate(params):
                # TODO: implement keyword and infty params
                # TODO: heap alloc function später checken
                body.sym[name].idx = len(node.free) + i

            (body_ret_reg,) = gen_reg({"R0"})
            code_c(body, lmbd, body_ret_reg, {"R0"}, code_v)
            lmbd[lambda_l] = [
                ("label", lambda_l),
                *body.code,
                ("=", "R0", body_ret_reg),
                ("ret",),
            ]

            node.code = [
                ("comment", f"lambda start {lambda_l}"),
                *env,
                ("mk[]", "*", ret, 2),
                ("[]=", ret, 0, lambda_l),
                ("[]=", ret, 1, env_reg),
                ("comment", f"lambda end {lambda_l}"),
            ]

        case "call", func, args:
            code_c(func, lmbd, ret, used, code_v)
            env_reg, arg_reg = gen_reg(used | {ret}, 2)

            (call_l,) = next(LABELS["call"])

            argvec = [("mk[]", "*", env_reg, len(args))]
            for i, argument in enumerate(args):
                match argument:
                    case "pos", expr:
                        argvec += code_c(
                            expr,
                            lmbd,
                            arg_reg,
                            used | {ret, env_reg},
                            code_v,
                        )
                        argvec += [("[]=", env_reg, i, arg_reg)]
                    case "keyword", var_name, expr:
                        argvec += code_c(
                            expr,
                            lmbd,
                            arg_reg,
                            used | {ret, env_reg},
                            code_v,
                        )
                        argvec += [("[]=", env_reg, func.sym[var_name].idx, arg_reg)]
            argvec += [
                ("=[]", "[*]", arg_reg, ret, 1),
                ("veccat", env_reg, arg_reg, env_reg),
                ("=[]", "i64", arg_reg, ret, 0),
            ]

            node.code = [
                ("comment", f"call start {call_l}"),
                *func.code,
                *argvec,
                ("fenter", env_reg),
                ("call", arg_reg),
                ("fleave",),
                ("=", ret, "R0"),
                ("comment", f"call end {call_l}"),
            ]

        case _:
            raise Exception(f"code_v not implemented for this AST node: {node.ast}")
    return node.code


def free(node) -> Any:
    node.free = set()
    match node.ast:
        case "program", body:
            free(body)
            node.free |= body.free
        case "num" | "float" | "str" | "complex", _:
            pass
        case "array", elements:
            for element in elements:
                free(element)
                node.free |= element.free
        case "array_access", array, index:
            free(array)
            free(index)
            node.free |= array.free | index.free
        case "unary", _, expr:
            free(expr)
            node.free |= expr.free
        case "binop", _, lhs, rhs:
            free(lhs)
            free(rhs)
            node.free |= lhs.free | rhs.free
        case "comparison", f, x, y:
            ops, exprs, tmp = [f], [x], y
            while tmp[0] == "comparison":
                ops.append(tmp[1])
                exprs.append(tmp[2])
                tmp = tmp[3]
            exprs.append(tmp)
            for expr in exprs:
                free(expr)
                node.free |= expr.free
        case "var", a:
            node.free = {a}
        case "assign", _, name, value:
            free(value)
            node.free |= value.free | {name}
        case "seq", exprs:
            for expr in exprs:
                free(expr)
                node.free |= expr.free
        case "if", cond, then_body, else_body:
            free(cond)
            free(then_body)
            node.free |= cond.free | then_body.free
            for elif_cond, e_body in else_body[:-1]:
                free(elif_cond)
                free(e_body)
                node.free |= elif_cond.free | e_body.free
            if else_body and else_body[-1][0] == "else":
                free(else_body[-1][1])
                node.free |= else_body[-1][1].free
        case "while", cond, body:
            free(cond)
            free(body)
            node.free |= cond.free | body.free
        case "loop", counter, interval, body:
            free(interval)
            free(body)
            node.free |= body.free | interval.free | {counter}
        case "interval", _, e1, e2, _:
            free(e1)
            free(e2)
            node.free |= e1.free | e2.free
        case "letrec", assignments, body:
            free(body)
            names = {name for *_, name, _ in assignments}
            node.free |= body.free
            for _, _, name, value in assignments:
                free(value)
                node.free |= value.free
            node.free -= names
        case "lambda", params, body, _:
            free(body)
            node.free |= body.free
            for param in params:
                match param:
                    case "pos", _, name:
                        node.free -= {name}
                    case "keyword", _, name, _:
                        node.free -= {name}
                    case "infty", _, name:
                        node.free -= {name}
        case "call", func, args:
            free(func)
            node.free |= func.free
            for arg in args:
                match arg:
                    case "pos", expr:
                        free(expr)
                        node.free |= expr.free
                    case "keyword", a, _:
                        free(a)
                        node.free |= a.free
        case _:
            raise NotImplementedError("free not implemented for this AST node")


def write_iic(code, fn="iic_code.iic"):
    with open(fn, "w") as f:
        f.write("\n".join(map(tuple_to_infix, code)))
