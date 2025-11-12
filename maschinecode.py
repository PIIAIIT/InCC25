def maschine_code(node):
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
    asm = []

    def regs(reg):
        if reg in register_mapping.keys():
            return register_mapping[reg]
        else:
            return reg

    OPS = {
        "+": "add",
        "-": "sub",
        "*": "imul",
    }

    for instr in node:
        match instr:
            case "label", "main":
                # entry point
                asm += ["global _start", "section .text", "_start:"]
            case "label", label_l:
                asm += ["global " + label_l, "section .text", label_l + ":"]
            case "=", register, expr:
                r = regs(register)
                e = regs(expr)
                asm += [f"mov {r}, {e}"]
            case "+" | "-" | "*" as op, res, reg1, reg2:
                asm += [
                    f"mov rax, {regs(reg1)}",
                    f"{OPS[op]} rax, {regs(reg2)}",
                    f"mov {regs(res)}, rax",
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

    # exit syscall
    asm += ["mov rax, 60", f"mov rdi, {register_mapping['R0']}", "syscall"]

    return asm


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
    with open("out.asm", "w") as f:
        for x in asm:
            f.write(x)
            f.write("\n")
