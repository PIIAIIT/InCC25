import subprocess
from ice2_ws25.ice_machine import find_labels
from zwischencode import Inst


def maschine_code(node: list[Inst], libICE=False):
    register_mapping = {
        "R0": "r15",
        "R1": "r14",
        "R2": "r13",
        "R3": "r12",
        "R4": "r11",
        "R5": "r10",
        "R6": "r9",
        "R7": "r8",
    }
    labels = find_labels(node)

    def return_label():
        count = 0
        while True:
            yield (f"ret_label_{count}",)
            count += 1

    return_l = return_label()

    # find all used registers
    saved_registers = set()
    for instr in node:
        for part in instr:
            if isinstance(part, str) and part in register_mapping:
                saved_registers.add(register_mapping[part])
    saved_registers = list(saved_registers)
    saved_registers.sort()

    externe = [
        "extern malloc" if not libICE else "extern ice_alloc",
        "extern printf" if not libICE else "extern ice_printf",
        "",
        "section .data",
        # "extern t_i64",
        # "extern t_f64",
        # "extern t_c64",
        # "extern t_str",
        "type_i64 dq 'i64    ', 0",
        "type_f64 dq 'f64    ', 0",
        "type_c64 dq 'c64    ', 0",
        "type_str dq 'str    ', 0",
        "type_ptr dq 'ptr    ', 0",
        "fmt: db '%ld', 10, 0",
        "debug: db 'D: %ld', 10, 0",
    ]
    asm = ["global main", *externe, "section .text"]

    # print result
    def asm_print(reg, fmt="debug"):
        return [
            f"mov rdi, {fmt}",
            f"mov rsi, {reg}",
            "xor rax, rax",
            "call printf" if not libICE else "call ice_printf",
        ]

    def regs(reg):
        if reg in register_mapping.keys():
            return register_mapping[reg]
        elif reg in labels:
            return f"{reg}"
        else:
            return reg

    def reg_index(ret_reg, index, ty_size):
        return [
            f"mov {regs(ret_reg)}, {regs(index)}",
            f"imul rbx, {regs(ty_size)}",
            "add rbx, 16",
        ]

    def call_malloc(type_size_reg, n, ret_ret):
        code = []
        aligned = len(saved_registers) % 2 == 1

        for reg in saved_registers:
            code += [f"push {reg}"]
        code += ["push rbp"]
        if aligned:
            code += ["sub rsp, 8"]

        if libICE:
            code += [
                f"mov rdi, {regs(type_size_reg)}",
                f"imul rdi, {regs(n)}",
                "add rdi, 16",
                f"mov rsi, {regs(n)}",
                "call ice_alloc",
            ]
        else:
            code += [
                f"mov rdi, {regs(type_size_reg)}",
                f"imul rdi, {regs(n)}",
                "add rdi, 16",
                "call malloc",
            ]

        if aligned:
            code += ["add rsp, 8"]
        code += ["pop rbp"]
        for reg in reversed(saved_registers):
            code += [f"pop {reg}"]

        code += [f"mov {regs(ret_ret)}, rax"]
        return code

    for instr in node:
        print(instr)
        match instr:
            case "label", "main":
                asm += ["main:"]
                asm += ["push rbp"] if libICE else []
            case "label", label_l:
                asm += [f"{label_l}:"]
            case "=", register, expr:
                r = regs(register)
                e = regs(expr)
                asm += [f"mov {r}, {e}"]
            case "+" | "-" | "*" | "xor" | "and" | "or" as op, res, reg1, reg2:
                OPS = {
                    "+": "add",
                    "-": "sub",
                    "*": "imul",
                    "xor": "xor",
                    "or": "or",
                    "and": "and",
                }
                asm += [f"{OPS[op]} {regs(reg1)}, {regs(reg2)}"]
                asm += [f"mov {regs(res)}, {regs(reg1)}"]
            case "not", res, reg1:
                if res == reg1:
                    asm += [f"xor {regs(res)}, 1"]
                else:
                    asm += [
                        f"mov {regs(res)}, {regs(reg1)}",
                        f"xor {regs(res)}, 1",
                    ]
            case "%", res, reg1, reg2:
                asm += [
                    f"mov rax, {regs(reg1)}",
                    "cqo",
                    f"mov rbx, {regs(reg2)}",
                    "idiv rbx",
                    f"mov {regs(res)}, rdx",
                ]
            case "/", res, reg1, reg2:
                asm += [
                    f"mov rax, {regs(reg1)}",
                    f"mov rbx, {regs(reg2)}",
                    "xor rdx, rdx",
                    "idiv rbx",
                    f"mov {regs(res)}, rax",
                ]
            case "\\", res, reg1, imm2:
                asm += [
                    f"mov rax, {regs(reg1)}",
                    f"mov rcx, {regs(imm2)}",
                    "shr rax, cl",
                    f"mov {regs(res)}, rax",
                ]
            # case "|", res, reg1, imm2:
            #     asm += [
            #         f"mov rax, {regs(reg1)}",
            #         f"mov rcx, {regs(imm2)}",
            #         "shl rax, cl",
            #         f"mov {regs(res)}, rax",
            #     ]
            case "**", res, reg1, imm2:
                asm += [
                    f"mov {regs(res)}, 1",
                    f"mov rcx, {regs(imm2)}",
                    f"mov rax, {regs(reg1)}",
                    f"pow_loop_{res}:",
                    "mul rax",
                    f"loop pow_loop_{res}",
                    f"mov {regs(res)}, rax",
                ]
            case "exp", res, reg1, reg2:
                asm += [
                    f"mov rax, {regs(reg1)}",
                    f"mov rbx, {regs(reg2)}",
                    f"pow_loop_{res}:",
                    "mul rax",
                    "dec rbx",
                    f"jnz pow_loop_{res}",
                    f"mov {regs(res)}, rax",
                ]
            case "u-", res, reg1:
                asm += [
                    f"mov rax, {regs(reg1)}",
                    "neg rax",
                    f"mov {regs(res)}, rax",
                ]
            case "u+", res, reg1:
                asm += [
                    f"mov rax, {regs(reg1)}",
                    f"mov {regs(res)}, rax",
                ]
            case "i+", res, reg1:
                pass
            case "<" | "<=" | ">" | ">=" | "==" | "!=" as cmp_op, res, reg1, reg2:
                CMPS = {
                    "<": "l",
                    "<=": "le",
                    ">": "g",
                    ">=": "ge",
                    "==": "e",
                    "!=": "ne",
                }
                asm += [
                    f"mov rax, {regs(reg1)}",
                    f"cmp rax, {regs(reg2)}",
                    f"set{CMPS[cmp_op]} al",
                    f"movzx {regs(res)}, al",
                ]
            case "ifgoto", cond, label:
                asm += [
                    f"cmp {regs(cond)}, 1",
                    f"je {label}",
                ]
            case "goto", label:
                asm += [f"jmp {label}"]
            case "comment", text:
                asm += [f";; {text}"]
            case "mk[]", res, arg1:
                asm += ["mov rdi, 24"]
                asm += [] if not libICE else ["mov rsi, 1"]
                asm += [
                    f"mov rbx, {regs(arg1)}",
                    "call malloc" if not libICE else "call ice_alloc",
                    f"mov {regs(res)}, rax",
                    # Oject schreiben
                    "mov rax, [rel type_i64]",  # TODO: type bestimmen
                    f"mov [{regs(res)}], rax",  # type header
                    f"mov dword [{regs(res)}+8], 8",  # type size
                    f"mov dword [{regs(res)}+12], 1",  # length
                    f"mov qword [{regs(res)}+16], rbx",  # first element
                ]
            case "mk[]", ty, res, n:

                def ty_conv(ty):
                    if ty.startswith("[]"):
                        return "type_ptr"
                    elif ty in {"i64", "f64", "c64", "str"}:
                        return "type_" + ty
                    elif ty in {"t_char", "*"}:
                        return "type_i64"
                    else:
                        return ty

                asm += [f"mov rdi, {16+8*n}"]
                asm += [] if not libICE else [f"mov rsi, {n}"]
                asm += [
                    "call malloc" if not libICE else "call ice_alloc",
                    f"mov {regs(res)}, rax",
                    # Oject schreiben
                    f"mov rax, [rel {ty_conv(ty)}]",  # TODO: type bestimmen
                    f"mov [{regs(res)}], rax",  # type header
                    f"mov dword [{regs(res)}+8], {1 if ty == "t_char" else 8}",  # type size
                    f"mov dword [{regs(res)}+12], {n}",  # length
                ]
            case "get", res, arg1:
                asm += [
                    f"mov {regs(res)}, [{regs(arg1)}+16]",  # get first element
                ]
            case "rewrite", arg1, arg2:
                asm += [
                    f"mov rdi, {regs(arg1)}",
                    f"mov rsi, {regs(arg2)}",
                    "mov eax, dword [rsi+8]",  # size
                    "mov ecx, dword [rsi+12]",  # length
                    "imul ecx, eax",  # size * length
                    "add rdi, 16",
                    "add rsi, 16",
                    "rep movsb",
                ]
            case "[]=", "V", i, val:
                asm += reg_index("rbx", i, 8)
                if val in labels:
                    asm += [
                        f"lea rax, {regs(val)}",
                        "mov qword [rbp+rbx], rax",
                    ]
                else:
                    asm += [f"mov qword [rbp+rbx], {regs(val)}"]
            case "[]=", vec, i, val:
                asm += reg_index("rbx", i, 8)
                if val in labels:
                    asm += [
                        f"lea rax, {regs(val)}",
                        f"mov qword [{regs(vec)}+rbx], rax",
                    ]
                else:
                    asm += [f"mov qword [{regs(vec)}+rbx], {regs(val)}"]
            case "=[]", res, "V", i:
                asm += reg_index("rbx", i, 8)
                asm += [f"mov {regs(res)}, [rbp+rbx]"]
            case "=[]", res, vec, i:
                asm += reg_index("rbx", i, 8)
                asm += [f"mov {regs(res)}, [{regs(vec)}+rbx]"]
            case "=[]", _, res, "V", i:
                asm += reg_index("rbx", i, 8)
                asm += [f"mov {regs(res)}, [rbp+rbx]"]
            case "=[]", _, res, vec, i:
                asm += reg_index("rbx", i, 8)
                asm += [f"mov {regs(res)}, [{regs(vec)}+rbx]"]
            case "veccat", res, vec1, vec2:
                asm += [
                    f"mov eax, dword [{regs(vec1)}+8]",  # typsize vec1
                    f"mov ebx, dword [{regs(vec1)}+12]",  # length vec1
                    f"mov ecx, dword [{regs(vec2)}+12]",  # length vec2
                    "add ecx, ebx",  # total length
                    "imul eax, ecx",  # total size in bytes
                    "add eax, 16",  # + header
                    "mov rdi, rax",
                ]
                asm += [] if not libICE else ["mov rsi, ecx"]  # TODO: für libICE
                asm += [
                    "call malloc" if not libICE else "call ice_alloc",
                    "mov rbx, rax",
                    # set header
                    "mov rdx, [rel type_i64]",
                    "mov [rbx], rdx",
                    f"mov edx, dword [{regs(vec1)}+8]",  # typsize vec1
                    "mov dword [rbx+8], edx",  # type size
                    "mov dword [rbx+12], ecx",  # total length
                    # copy vec1
                    "lea rdi, [rbx+16]",  # data res
                    f"lea rsi, [{regs(vec1)}+16]",  # data vec1
                    f"mov ecx, dword [{regs(vec1)}+12]",  # length vec1
                    "imul ecx, edx",  # size in bytes
                    "rep movsb",
                    # copy vec2
                    # offset res
                    "lea rdi, [rdi+rcx]",  # data res + offset
                    f"lea rsi, [{regs(vec2)}+16]",
                    f"mov edx, dword [{regs(vec2)}+8]",
                    f"mov ecx, dword [{regs(vec2)}+12]",
                    "imul ecx, edx",
                    "rep movsb",
                    f"mov {regs(res)}, rbx",
                ]
            case "enter", reg:
                asm += [
                    "push rbp",
                    f"mov rbp, {regs(reg)}",
                ]
            case "leave",:
                asm += ["pop rbp"]
            case "fenter", arg:
                for reg in saved_registers:
                    asm += [f"push {reg}"]
                if len(saved_registers) % 2 == 1:
                    asm += ["push rbx"]
                asm += [
                    "push rbp",
                    f"mov rbp, {regs(arg)}",
                ]
                asm += ["sub rsp, 8"]
            case "fleave",:
                asm += ["add rsp, 8"]
                asm += [
                    f"mov rax, {register_mapping['R0']}"
                ]  # return value of function
                asm += ["pop rbp"]
                for reg in reversed(saved_registers):
                    asm += [f"pop {reg}"]
                if len(saved_registers) % 2 == 1:
                    asm += ["pop rbx"]
                asm += [f"mov {register_mapping['R0']}, rax"]
            case "ret",:
                asm += ["ret"]
            case "call", fct:
                (nl,) = next(return_l)
                asm += [
                    f"lea rax, [rel {nl}]",
                    "push rax",
                    f"jmp {regs(fct)}",
                    f"{nl}:",
                ]
            case _:
                raise ValueError(f"Unknown instruction: {instr}")

    asm += asm_print(register_mapping["R0"], "fmt")
    # exit syscall
    asm += ["mov rax, 60", "mov rdi, 0", "syscall"]
    asm += ["ret"]

    return asm


def format_asm(asm):
    formatted = ""
    for line in asm:
        match line:
            case line if line.strip() == "":
                formatted += "\n"
            case label if label.endswith(":"):
                formatted += f"{label}\n"
            case line if line.startswith(";"):
                formatted += f"{line}\n"
            case line if (
                line.startswith("section")
                or line.startswith("global")
                or line.startswith("extern")
            ):
                formatted += f"{line}\n"
            case _:
                formatted += f"    {line}\n"
    return formatted


def write_to_file(asm, filename="out.asm"):
    with open(filename, "w") as f:
        f.write(format_asm(asm))


if __name__ == "__main__":
    example = [
        ("label", "main"),
        ("=", "R0", 3),
        ("=", "R2", 12),
        ("+", "R1", "R0", "R2"),
        ("=", "R0", 4),
        ("=", "R3", 2),
        ("*", "R2", "R0", "R3"),
        ("+", "R0", "R1", "R2"),
        ("=", "R0", "R0"),
    ]
    for x in example:
        print(x)
    asm = maschine_code(example)

    for x in asm:
        print(x)

    # print to file
    write_to_file(asm)

    # assemble and link
    subprocess.run(["nasm", "-felf64", "out.asm", "-o", "out.o"])
    subprocess.run(["ld", "out.o", "-o", "out"])
