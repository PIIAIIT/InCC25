# ---------------- FUNKTIONS FOR PARSER ----------------
def generator():
    count = dict()

    def gen(name):
        nonlocal count
        if name not in count:
            count[name] = 0
        else:
            count[name] += 1
        return name + str(count[name])

    return gen


# ---------------- FUNKTIONS FOR PARSER ----------------


# ---------------- FUNKTIONS FOR INTERPRETER ----------------
def iter_tuple(t):
    while isinstance(t, tuple):
        yield t[0]
        t = t[1]


def binop_for_lists(x, y, func):
    if isinstance(x, list) or isinstance(y, list):
        return [
            func(i, j)
            for i, j in zip(
                x if isinstance(x, list) else [x] * len(y),
                y if isinstance(y, list) else [y] * len(x),
            )
        ]
    return None


def binop_for_tuples(x, y, func):
    if isinstance(x, tuple) and isinstance(y, tuple):
        # (1, (2, (3, None))) + (2, (3, (4, None)))
        a = x[0] if isinstance(x, tuple) else x
        b = y[0] if isinstance(y, tuple) else y

        if a is None or b is None:
            return y if b is None else x

        next_x = x[1] if isinstance(x, tuple) and x[1] is not None else None
        next_y = y[1] if isinstance(y, tuple) and y[1] is not None else None

        next_pair = binop_for_tuples(next_x, next_y, func) if next_x or next_y else None
        return (func(a, b), next_pair)
    if isinstance(x, tuple) or isinstance(y, tuple):
        # (1, (2, (3, None))) + 2
        # 2 + (1, (2, (3, None)))
        a = x[0] if isinstance(x, tuple) else y[0]
        b = x if not isinstance(x, tuple) else y

        next = (
            x[1]
            if isinstance(x, tuple) and x[1] is not None
            else y[1] if isinstance(y, tuple) and y[1] is not None else None
        )

        next_pair = binop_for_tuples(next, b, func) if next else None
        return (func(a, b), next_pair)

    return None


# ---------------- FUNKTIONS FOR INTERPRETER ----------------


# ---------------- FUNKTIONS FOR ZWISCHENCODE ----------------


def gen_label(*prefixes):
    count = 0
    while True:
        count += 1
        yield tuple(f"{prefix}_{count}" for prefix in prefixes)


def gen_reg(used, n=1):
    regs = []
    i = 0
    while len(regs) < n:
        reg = f"R{i}"
        if reg not in used:
            regs.append(reg)
        i += 1
    return tuple(regs)


def save_in_file(iic_code, filename="iic_code.iic"):
    with open(filename, "w") as f:
        for line in iic_code:
            if isinstance(line, tuple):
                line = " ".join(line)
            f.write(line + "\n")


# ---------------- FUNKTIONS FOR ZWISCHENCODE ----------------
