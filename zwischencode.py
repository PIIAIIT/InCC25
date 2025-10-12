from parser import look_up_table, unary

OPS = {v: k for k, v in look_up_table.items()}
OPS.update({v: k for k, v in unary.items()})


def __trav_ast_b(ast, iic_code, reg_base=0, b_tuple=False, b_root=False):
    match ast:
        case ("num", value):
            target_reg = f"R{reg_base}"
            if b_root:
                iic_code.append(
                    f"{target_reg} = {value}"
                    if not b_tuple
                    else ("=", target_reg, str(value))
                )
                return target_reg, reg_base
            return str(value), reg_base

        case (kind, op, left, right) if kind in {"binop", "comparison"}:
            left_val, _ = __trav_ast_b(left, iic_code, reg_base, b_tuple)
            right_val, _ = __trav_ast_b(right, iic_code, reg_base + 1, b_tuple)
            target_reg = f"R{reg_base}"
            iic_code.append(
                f"{target_reg} = {left_val} {OPS[op]} {right_val}"
                if not b_tuple
                else (op, target_reg, left_val, right_val)
            )
            return target_reg, reg_base

        case ("seq", exprs):
            result = None
            current_reg = reg_base
            for expr in exprs:
                result, current_reg = __trav_ast_b(
                    expr, iic_code, current_reg, b_tuple, b_root
                )
            return result, current_reg

        case ("if", condition, then_body, [("else", else_body)]):
            cond_val, _ = __trav_ast_b(condition, iic_code, reg_base, b_tuple)
            label_then = f"L{len(iic_code)}_then"
            label_else = f"L{len(iic_code)}_else"
            label_end = f"L{len(iic_code)}_end"
            iic_code.append(
                f"IF {cond_val} GOTO {label_then}"
                if not b_tuple
                else ("IFGOTO", cond_val, label_then)
            )
            iic_code.append(
                f"GOTO {label_else}" if not b_tuple else ("GOTO", label_else)
            )
            iic_code.append(f"{label_then}:" if not b_tuple else ("label", label_then))
            then_val, _ = __trav_ast_b(then_body, iic_code, reg_base, b_tuple)
            target_reg = f"R{reg_base}"
            iic_code.append(
                f"{target_reg} = {then_val}"
                if not b_tuple
                else ("=", target_reg, then_val)
            )
            iic_code.append(f"GOTO {label_end}" if not b_tuple else ("GOTO", label_end))
            iic_code.append(f"{label_else}:" if not b_tuple else ("label", label_else))
            else_val, _ = __trav_ast_b(else_body, iic_code, reg_base, b_tuple)
            target_reg = f"R{reg_base}"
            iic_code.append(
                f"{target_reg} = {else_val}"
                if not b_tuple
                else ("=", target_reg, else_val)
            )
            iic_code.append(f"{label_end}:" if not b_tuple else ("label", label_end))
            return target_reg, reg_base

        case _:
            # print(f"Unknown AST node: {ast}")
            raise ValueError(f"Unknown AST node: {ast}")


def code_b(ast, b_tuple=False, b_save_in_file=False, filename="iic_code.iic"):
    iic_code = ["main:"] if not b_tuple else [("label", "main")]
    __trav_ast_b(ast, iic_code, b_tuple=b_tuple, b_root=True)
    save_in_file(iic_code, filename) if b_save_in_file else None
    return iic_code


def save_in_file(iic_code, filename="iic_code.iic"):
    with open(filename, "w") as f:
        for line in iic_code:
            if isinstance(line, tuple):
                line = " ".join(line)
            f.write(line + "\n")


if __name__ == "__main__":
    ast = (
        "binop",
        "+",
        ("binop", "*", ("num", 2), ("num", 3)),
        ("binop", "-", ("num", 10), ("num", 4)),
    )
    print("AST:", ast)
    for line in code_b(ast):
        print(line)
    ast_seq = (
        "seq",
        [
            ("binop", "+", ("num", 1), ("num", 2)),
            ("binop", "*", ("num", 3), ("num", 4)),
            ("binop", "-", ("num", 5), ("num", 6)),
        ],
    )
    print("AST:", ast_seq)
    for line in code_b(ast_seq):
        print(line)

    ast_complex = (
        "binop",
        "+",
        ("binop", "*", ("num", 2), ("binop", "-", ("num", 10), ("num", 4))),
        ("binop", "/", ("num", 20), ("num", 5)),
    )
    print("AST:", ast_complex)
    for line in code_b(ast_complex):
        print(line)

    # (3 + (3+4)*5-1+24*2) / 2
    ast_complex2 = (
        "binop",
        "/",
        (
            "binop",
            "+",
            (
                "binop",
                "-",
                (
                    "binop",
                    "+",
                    ("num", 3),
                    ("binop", "*", ("binop", "+", ("num", 3), ("num", 4)), ("num", 5)),
                ),
                ("num", 1),
            ),
            ("binop", "*", ("num", 24), ("num", 2)),
        ),
        ("num", 2),
    )
    print("AST:", ast_complex2)
    for line in code_b(ast_complex2):
        print(line)

    # Very complex tree with all numbers from 1 to 16
    ast_complete_tree = (
        "binop",
        "+",
        (
            "binop",
            "+",
            (
                "binop",
                "+",
                ("binop", "+", ("num", 1), ("num", 2)),
                ("binop", "+", ("num", 3), ("num", 4)),
            ),
            (
                "binop",
                "+",
                ("binop", "+", ("num", 5), ("num", 6)),
                ("binop", "+", ("num", 7), ("num", 8)),
            ),
        ),
        (
            "binop",
            "+",
            (
                "binop",
                "+",
                ("binop", "+", ("num", 9), ("num", 10)),
                ("binop", "+", ("num", 11), ("num", 12)),
            ),
            (
                "binop",
                "+",
                ("binop", "+", ("num", 13), ("num", 14)),
                ("binop", "+", ("num", 15), ("num", 16)),
            ),
        ),
    )
    print("AST:", ast_complete_tree)
    for line in code_b(ast_complete_tree, b_tuple=True):
        print(line)

    ast_if = (
        "if",
        ("binop", "==", ("num", 1), ("num", 2)),
        ("num", 41),
        [("else", ("num", 42))],
    )
    print("AST:", ast_if)
    for line in code_b(ast_if, b_tuple=True):
        print(line)
