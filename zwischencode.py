from parser import Node
from typing import Any
from utils import gen_label, gen_reg, save_in_file

# Seiden und Willhelm Buch
# Nx python bib

DEBUG = False

OPS = {
    "plus": "+",
    "minus": "-",
    "times": "*",
    "divide": "|",
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
    "uminus": "u-",
    "uplus": "u+",
}


if_label = gen_label("if", "else", "end_if")
elif_label = gen_label("elif", "elif_body")
while_label = gen_label("while", "end_while")
seq_label = gen_label("seq")
loop_label = gen_label("loop", "end_loop")
let_label = gen_label("letrec")
lambda_label = gen_label("lambda")

VAR_ID = 0


def code_c(node, lmbd, ret, used, code_x, scope="global"):
    match node.ast:
        case None:
            return []
        case ("program", expr):
            code_c(expr, lmbd, ret, used, code_x, scope=scope)
            node.code = [("label", "main"), *expr.code, ("=", "R0", "R0")]
        case "seq", exprs:
            (seq_l,) = next(seq_label)
            node.code = [("comment", f"seq start {seq_l}")]
            for expr in exprs[:-1]:
                node.code += code_c(expr, lmbd, ret, used, code_x, scope=scope)
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
            | "call",
            *_,
        ):
            code_x(node, lmbd, ret, used, scope=scope)

        case "if", condition, then_body, else_body:
            has_else = bool(else_body and else_body[-1][0] == "else")
            n_elifs = len(else_body) - (1 if has_else else 0)

            if_l, else_l, end_l = next(if_label)
            elif_cond_l = [next(elif_label)[0] for _ in range(n_elifs)]
            elif_body_l = [next(elif_label)[1] for _ in range(n_elifs)]

            code_c(condition, lmbd, ret, used, code_b)
            code_c(then_body, lmbd, ret, used, code_x)

            for i in range(n_elifs):
                cond, body = else_body[i]
                code_c(cond, lmbd, ret, used, code_x)
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
            while_l, end_l = next(while_label)
            (cond_reg,) = gen_reg(used | {ret})

            code_c(cond, lmbd, cond_reg, used | {ret}, code_b)
            code_c(body, lmbd, ret, used, code_x)

            node.code = [
                ("label", while_l),
                *cond.code,
                ("ifgoto", f"R{cond_reg}", end_l),
                *body.code,
                ("goto", while_l),
                ("label", end_l),
            ]

        case "loop", counter, interval, body:
            loop_l, end_l = next(loop_label)

            count_reg, cond_reg = gen_reg(used | {ret}, 2)

            code_c(counter, lmbd, ret, used, code_b)
            code_c(interval, lmbd, ret, used | {count_reg}, code_b)
            code_c(body, lmbd, ret, used | {count_reg, cond_reg}, code_x)

            node.code = [
                ("comment", f"count of {loop_l}"),
                *counter.code,
                *interval.code,
                ("label", loop_l),
                ("<=", cond_reg, count_reg, 0),
                ("ifgoto", cond_reg, end_l),
                ("-", count_reg, count_reg, 1),
                ("comment", f"body of {loop_l}"),
                *body.code,
                ("goto", loop_l),
                ("label", end_l),
            ]

        # TODO: letrec
        case "letrec", decls, body:
            body.sym.copy(body.free)
            for i, name in enumerate(body.free):
                body.sym[name].idx = i

            (letrec_l,) = next(let_label)
            (env_reg,) = gen_reg(used | {ret})

            gobal_vars = []
            for name in node.free:
                gobal_vars += [
                    ("get", ret, node.sym[name].idx),
                    ("[]=", env_reg, body.sym[name].idx, ret),
                ]

            hulls_code = []
            hulls_regs = []
            for _, ty, var_name, _ in decls:
                if var_name not in body.free:
                    continue
                (hull_reg,) = gen_reg(
                    used | {ret} | {env_reg} | {r for _, r in hulls_regs}
                )
                match ty:
                    case ("->", *_):
                        hulls_code += [("mk[]", "*", hull_reg, 2)]
                    case _:
                        hulls_code += [("mk[]", hull_reg, 0)]
                hulls_code += [("[]=", env_reg, body.sym[var_name].idx, hull_reg)]
                hulls_regs += [(var_name, hull_reg)]

            declared_vars = []
            for _, ty, name, rhs in decls:
                if name not in body.free:
                    declared_vars += code_c(rhs, lmbd, ret, used, code_v)
                    continue
                _, hull_reg = next(r for r in hulls_regs if r[0] == name)
                code_c(rhs, lmbd, ret, used | {env_reg} | {hull_reg}, code_v)
                declared_vars += rhs.code
                declared_vars += [("rewrite", hull_reg, ret)]

            code_c(body, lmbd, ret, used, code_v, scope="letrec")

            node.code = [
                ("comment", f"env of {letrec_l}"),
                ("mk[]", "*", env_reg, len(body.free)),
                ("comment", f"global vars of {letrec_l}"),
                *gobal_vars,
                ("comment", f"hulls of {letrec_l}"),
                *hulls_code,
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


def code_b(node: Node, lmbd, ret, used, scope="global") -> Any:
    match node.ast:
        case "seq", exprs:
            code_c(node, lmbd, ret, used, code_b)
        case "program", expr:
            code_c(expr, lmbd, ret, used, code_b)

        case "num" | "float" | "str" | "complex" as lit, value:
            _type = {
                "num": lambda x: int(x),
                "float": lambda x: float(x),
                "str": lambda x: x[1:-1] if x.startswith('"') else x,
                "complex": lambda x: complex(x),
            }
            node.code = [("=", ret, _type[lit](value))]

        case "var" | "call", name, *_:
            code_c(node, lmbd, ret, used, code_v, scope=scope)
            id = node.sym[name].idx
            if scope == "letrec" and name in node.free:
                id = ret
            node.code += [("get", ret, id)]

        case "assign", _, name, _:
            code_c(node, lmbd, ret, used, code_v)
            node.code += [("get", ret, node.sym[name].idx)]

        case "binop", "power", lhs, rhs:
            base_reg, exp_reg, tmp_reg = gen_reg(used | {ret}, 3)
            loop_label, end_label = next(gen_label("power_loop", "power_end"))

            code_c(lhs, lmbd, base_reg, used | {ret}, code_b)
            code_c(rhs, lmbd, exp_reg, used | {ret, base_reg}, code_b)

            node.code = [
                *lhs.code,
                *rhs.code,
                ("=", ret, 1),
                ("=", tmp_reg, 0),
                ("label", loop_label),
                (">=", "Rcmp", tmp_reg, exp_reg),
                ("ifgoto", "Rcmp", end_label),
                ("*", ret, ret, base_reg),
                ("+", tmp_reg, tmp_reg, 1),
                ("goto", loop_label),
                ("label", end_label),
            ]
        # case "binop", "mod", lhs, rhs:
        #     node.code = [
        #         *code_b(lhs, reg_base).code,
        #         *code_b(rhs, reg_base + 1).code,
        #         ("\\", f"R{reg_base + 2}", f"R{reg_base}", f"R{reg_base + 1}"),
        #         ("*", f"R{reg_base + 2}", f"R{reg_base + 2}", f"R{reg_base + 1}"),
        #         ("-", f"R{reg_base}", f"R{reg_base}", f"R{reg_base + 2}"),
        #         ("+", target_reg, f"R{reg_base}", f"R{reg_base + 1}"),
        #     ]
        # case "binop", "exp", lhs, rhs:
        #     node.code = [
        #         *code_b(lhs, reg_base).code,
        #         *code_b(
        #             Node("binop", "power", Node("num", 10), rhs), reg_base + 1
        #         ).code,
        #         ("*", target_reg, f"R{reg_base}", f"R{reg_base + 1}"),
        #     ]
        # case "binop", "xor", lhs, rhs:
        #     node.code = [
        #         *code_b(lhs, reg_base).code,
        #         *code_b(rhs, reg_base + 1).code,
        #         ("or", target_reg, f"R{reg_base}", f"R{reg_base + 1}"),
        #         ("and", "R_temp", f"R{reg_base}", f"R{reg_base + 1}"),
        #         ("not", "R_temp", "R_temp"),
        #         ("and", target_reg, target_reg, "R_temp"),
        #     ]

        case "binop", op, lhs, rhs:
            x_reg, y_reg = gen_reg(used | {ret}, 2)

            code_c(lhs, lmbd, x_reg, used, code_b)
            code_c(rhs, lmbd, y_reg, used | {x_reg}, code_b)

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

            tmp_regs = list(gen_reg(used | {ret}, len(exprs)))

            code_c(exprs[0], lmbd, tmp_regs[0], used, code_b)
            code_c(exprs[1], lmbd, tmp_regs[1], used | {tmp_regs[0]}, code_b)

            code = [
                *exprs[0].code,
                *exprs[1].code,
                (OPS[ops[0]], ret, tmp_regs[0], tmp_regs[1]),
            ]

            for i in range(1, len(ops)):
                code_c(
                    exprs[i + 1], lmbd, tmp_regs[i + 1], used | set(tmp_regs), code_b
                )
                code += exprs[i + 1].code
                code += [
                    (OPS[ops[i]], tmp_regs[i + 1], tmp_regs[i], tmp_regs[i + 1]),
                    ("and", ret, ret, tmp_regs[i + 1]),
                ]
            node.code = code
        case _:
            raise Exception("code_b not implemented for this AST node")


def code_v(node: Node, lmbd, ret, used, scope="global") -> Any:
    match node.ast:
        case "num" | "str" | "float", _:
            code_c(node, lmbd, ret, used, code_b)
            node.code += [("mk[]", ret, ret)]

        case "binop" | "unary", *_:
            code_c(node, lmbd, ret, used, code_b)
            node.code += [("mk[]", ret, ret)]

        case "var", name:
            node.code = [("comment", f"var: {name}")]
            if scope == "letrec":
                node.code += [
                    ("=[]", node.sym[name].ty, ret, "V", node.sym[name].idx),
                ]

        case "assign", _, name, value:
            global VAR_ID
            code_c(value, lmbd, ret, used, code_v)
            node.sym[name].idx = VAR_ID
            VAR_ID += 1
            node.code = value.code + [("rewrite", ret, ret)]

        case "lambda", params, body, _:
            # rekursion kann noch warten
            body.sym.copy(body.free)

            (lambda_l,) = next(lambda_label)

            (env_reg,) = gen_reg(used | {ret})
            env = [("mk[]", "*", env_reg, len(body.free))]
            for i, name in enumerate(body.free):
                body.sym[name].idx = i
                env += [
                    ("=[]", node.sym[name].ty, ret, "V", node.sym[name].idx),
                    ("get", ret, ret),
                    ("[]=", env_reg, i, ret),
                ]

            for i, (*_, name) in enumerate(params):
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
                ("[]=", ret, 0, env_reg),
                ("[]=", ret, 1, lambda_l),
                ("comment", f"lambda end {lambda_l}"),
            ]

        case "call", func, args:
            code_c(func, lmbd, ret, used, code_v)

            env_reg, arg_reg = gen_reg(used | {ret}, 2)

            argvec = [
                ("mk[]", "*", arg_reg, len(args)),
            ]
            for i, arg in enumerate(args):
                match arg:
                    case "pos", expr:
                        argvec += code_c(
                            expr, lmbd, arg_reg, used | {ret, arg_reg}, code_v
                        ) + [
                            ("[]=", arg_reg, i, arg_reg),
                        ]
                    case "keyword", _, a:
                        pass
            argvec += [
                ("=[]", arg_reg, ret, 1),
                ("veccat", env_reg, arg_reg, env_reg),
                ("=[]", arg_reg, ret, 0),
            ]
            if len(args) == len(func.ty[1]):
                node.code = [
                    ("comment", f"call start {func}"),
                    *func.code,
                    *argvec,
                    ("fenter", env_reg),
                    ("call", arg_reg),
                    ("fleave",),
                    ("=", ret, "R0"),
                ]
            else:
                node.code = [
                    ("comment", f"call start {func}"),
                    *func.code,
                    *argvec,
                    ("mk[]", "*", ret, 2),
                    ("[]=", ret, 0, env_reg),
                    ("[]=", ret, 1, arg_reg),
                ]
        case _:
            raise Exception("code_v not implemented for this AST node")
    return node.code


def free(node) -> Any:
    node.free = set()
    match node.ast:
        case "num" | "float" | "str" | "complex", _:
            pass
        case "program", body:
            free(body)
            node.free |= body.free
        case "var", a:
            node.free |= {a}
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


if __name__ == "__main__":
    from ice2_ws25 import ice_machine

    example = [
        ("label", "main"),
        ("comment", "env of letrec_1"),
        ("mk[]", "*", "R1", 2),
        ("comment", "global vars of letrec_1"),
        ("comment", "hulls of letrec_1"),
        ("mk[]", "R2", 0),
        ("[]=", "R1", 0, "R2"),
        ("mk[]", "R3", 0),
        ("[]=", "R1", 1, "R3"),
        ("enter", "R1"),
        ("comment", "declared vars of letrec_1"),
        ("=", "R0", 3),
        ("mk[]", "R0", "R0"),
        ("rewrite", "R2", "R0"),
        ("=", "R0", 5),
        ("mk[]", "R0", "R0"),
        ("rewrite", "R3", "R0"),
        ("comment", "body of letrec_1"),
        ("comment", "var: x"),
        ("=[]", "i64", "R1", "V", 0),
        ("get", "R1", "R1"),
        ("comment", "var: y"),
        ("=[]", "i64", "R2", "V", 1),
        ("get", "R2", "R2"),
        ("+", "R0", "R1", "R2"),
        ("mk[]", "R0", "R0"),
        ("leave",),
        ("comment", "end of letrec_1"),
        ("=", "R0", "R0"),
    ]
    ice_machine.run(example, debug=True, detailed=True)

    example1 = [
        ("label", "main"),
        ("comment", "seq start seq_1"),
        ("=", "R0", 3),
        ("mk[]", "R0", "R0"),
        ("rewrite", "R0", "R0"),
        ("get", "R0", 0),
        ("comment", "env of letrec_1"),
        ("mk[]", "*", "R1", 1),
        ("comment", "global vars of letrec_1"),
        ("comment", "hulls of letrec_1"),
        ("mk[]", "R2", 0),
        ("[]=", "R1", 0, "R2"),
        ("enter", "R1"),
        ("comment", "declared vars of letrec_1"),
        ("=", "R0", 5),
        ("mk[]", "R0", "R0"),
        ("rewrite", "R2", "R0"),
        ("comment", "body of letrec_1"),
        ("comment", "seq start seq_2"),
        ("comment", "env of letrec_2"),
        ("mk[]", "*", "R1", 2),
        ("comment", "global vars of letrec_2"),
        ("get", "R0", 0),
        ("[]=", "R1", 1, "R0"),
        ("comment", "hulls of letrec_2"),
        ("mk[]", "R2", 0),
        ("[]=", "R1", 0, "R2"),
        ("enter", "R1"),
        ("comment", "declared vars of letrec_2"),
        ("=", "R0", 7),
        ("mk[]", "R0", "R0"),
        ("rewrite", "R2", "R0"),
        ("comment", "body of letrec_2"),
        ("comment", "var: x"),
        ("=[]", "i64", "R1", "V", 0),
        ("get", "R1", "R1"),
        ("comment", "var: y"),
        ("=[]", "i64", "R2", "V", 0),
        ("get", "R2", "R2"),
        ("+", "R0", "R1", "R2"),
        ("mk[]", "R0", "R0"),
        ("leave",),
        ("comment", "end of letrec_2"),
        ("comment", "var: x"),
        ("=[]", "i64", "R0", "V", 0),
        ("comment", "seq end seq_2"),
        ("leave",),
        ("comment", "end of letrec_1"),
        ("comment", "var: x"),
        ("get", "R0", 0),
        ("comment", "seq end seq_1"),
        ("=", "R0", "R0"),
    ]
    # { i64 x := 3; sei i64 x := 5 in { sei i64 y := 7 in x+y .; x } .; x }

    ice_machine.run(example1, debug=True, detailed=True)
