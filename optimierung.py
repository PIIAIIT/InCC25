from graphviz import Digraph
from ice2_ws25.ice_machine import Inst, tuple_to_infix, reads, writes
from utils import generator

unique = generator()


### OPTIMIZATION ###
def optimize(iir, visual=False, debug=False):
    print("Optimizing...") if debug else None
    print("Control Flow Graph created.") if debug else None
    cfg = CFGraph(iir)
    if visual:
        cfg.visualize()

    liveness(cfg)
    spilling(cfg)

    cfg.print_cfg()

    return cfg.iir


def small_reg(cfg):
    used_regs = set()
    for line in cfg.iir:
        used_regs |= line.read | line.write
    reg_map = {reg: f"R{i}" for i, reg in enumerate(sorted(used_regs))}
    cfg.iir = [line.replace(reg_map) for line in cfg.iir]


def coloring(cfg, visual=False):
    for x, y in zip(cfg.part, cfg.last):
        cfg.iir[x : y + 1] = reg_color(cfg.iir[x : y + 1], visual)


# --------- CONTROL FLOW GRAPH ---------
class CFGraph:
    def __init__(self, iir):
        self.iir = iir
        part = set()
        jump = {(None, "main")}
        labs = dict()
        for i, x in enumerate(iir):
            match x:
                case ("ifgoto", _, label):
                    jump |= {(i, label), (i, i + 1)}
                case ("goto", label):
                    jump |= {(i, label)}
                case ("label", label):
                    labs[label] = i
                case ("ret",):
                    part |= {i + 1}
        for x, y in jump.copy():
            if isinstance(y, str):
                jump -= {(x, y)}
                jump |= {(x, y := labs[y])}
            part |= {y}
            if y == 0:
                continue
            match iir[y - 1]:
                case ("goto" | "ret", *_):
                    continue
                case _:
                    jump |= {(y - 1, y)}
        self.part = sorted(part | {0})
        self.jump = dict()
        for x, y in jump:
            if not (x and y):
                continue
            self.jump.setdefault(self.part.index(x + 1) - 1, []).append(
                self.part.index(y)
            )
        self.last = [x - 1 for x in self.part[1:]] + [len(iir) - 1]

    def print_cfg(self):
        """debuggind function to print the control flow graph and liveness info"""
        print("Control Flow Graph:")
        for i in range(len(self.part)):
            x, y = self.part[i], self.last[i]
            print(f"Block {i}: Instructions {x} to {y}")
            print("  Instructions:")
            for line in self.iir:
                print(f"    {line} \t\t {line.read=}, {line.write=}, {line.live=}")
            print("  Jumps to:", self.jump.get(i, []))
        print()

    def visualize(self):
        dot = Digraph(format="png")
        dot.attr(
            "node", fontname="FiraCode", shape="box", style="rounded", labeljust="l"
        )
        for i in range(n := len(self.part)):
            x, y = self.part[i], self.part[i + 1] if i < n - 1 else len(self.iir)
            dot.node(
                str(i), "".join([f"{tuple_to_infix(s)}\\l" for s in self.iir[x:y]])
            )
        for x, y in self.jump.items():
            for y in y:
                dot.edge(str(x), str(y))
        dot.render("dot/cfgraph", view=True)


def liveness(cfg):

    r = list(cfg.iir)
    iir = cfg.iir = [Inst(*entry) for entry in r]

    for line in iir:
        line.read = reads(line) - {"V"}
        line.write = writes(line) - {"V"}
        line.live = set()

    repeat = True
    while repeat:
        repeat = False
        for i, x in enumerate(cfg.part):

            for a in reversed(range(x + 1, cfg.last[i] + 1)):
                prev = iir[a - 1]
                succ = iir[a]
                new_line = (succ.live | succ.read) - prev.write
                if not new_line.issubset(prev.live):
                    iir[a - 1].live |= new_line
                    repeat = True

            for src, dest in cfg.jump.items():
                if i in dest:
                    a = cfg.last[src]
                    new_line = (iir[x].live | iir[x].read) - iir[a].write
                    if not new_line.issubset(iir[a].live):
                        iir[a].live |= new_line
                        repeat = True


#  --------- REGISTER ALLOCATION (GRAPH COLORING) ---------


def reg_color(iir, visual=False):
    edges = set()
    for e in ((x, y) for line in iir for x in line.write for y in line.live):
        edges |= {tuple(sorted(e))}
    nodes = set.union(*(line.read | line.write for line in iir))
    dep = dict()
    for x, y in edges:
        dep.setdefault(x, []).append(y)
        dep.setdefault(y, []).append(x)
    stk = sorted(nodes, key=lambda x: len(dep.get(x) or []))
    col = dict()
    while stk:
        reg = stk.pop()
        adj = set(col.get(x) for x in dep.get(reg) or []) - {None}
        for i, x in enumerate(sorted(adj)):
            if i != x:
                col[reg] = i
        else:
            col[reg] = len(adj)
    if visual:
        dot = Digraph(format="png")
        dot.attr(
            "node",
            fontname="FiraCode",
            shape="circle",
            style="filled",
            fontcolor="#eff1f5",
        )
        cpal = [
            "#1e66f5",
            "#40a02b",
            "#8839ef",
            "#d20f39",
            "#fe640b",
            "#df8e1d",
            "#ea76cb",
            "#4c4f69",
        ]
        for reg in nodes:
            dot.node(str(reg), str(reg), color=cpal[col[reg] % len(cpal)])
        for x, y in edges:
            dot.edge(str(x), str(y), dir="none")
        dot.render(unique("dot/reg_color"), view=True)
    # TODO: change this, because minimum doesnt work like intended on strings
    norm = {r: min(k for k, v in col.items() if v == val) for r, val in col.items()}
    return [line.replace(norm) for line in iir]


# ------------ SPILLING ------------
def spill_register(cfg, reg, spill_reg):
    for i in cfg.part:
        for a in range(i, cfg.last[cfg.part.index(i)] + 1):
            line = cfg.iir[a]
            print(f"{line=}, {line.read=}, {line.write=}")
            if reg in line.read:
                line_idx = cfg.iir.index(line)
                cfg.iir.insert(
                    line_idx,
                    Inst("=[]", spill_reg, "V", reg),
                )
            if reg in line.write:
                line_idx = cfg.iir.index(line) + 1
                cfg.iir.insert(
                    line_idx,
                    Inst("[]=", "V", reg, spill_reg),
                )


def spilling(cfg, threshold=4):
    # find registers to spill
    reg_usage = {}
    for line in cfg.iir:
        for r in line.read | line.write:
            reg_usage.setdefault(r, 0)
            reg_usage[r] += 1
    # spill registers used more than a threshold
    for r, usage in reg_usage.items():
        if usage > threshold:
            spill_register(cfg, r, f"spill_{r}")


# MIME
# def find_labels(tac):
#     labels = {}
#     for i, instruction in enumerate(tac):
#         match instruction:
#             case ("label", target_l):
#                 labels[target_l] = i
#     return labels
#
#
# def control_flow_graph(tac):
#     """
#     Erstellt einen Kontrollflussgraphen (CFG) aus dem gegebenen dreistelligen Zwischencode (TAC).
#     :param tac: Liste von TAC-Anweisungen
#     :return: Kontrollflussgraph als Dictionary
#     """
#     cfg = {}
#     labels = find_labels(tac)
#
#     for i, instruction in enumerate(tac):
#         match instruction:
#             case ("goto", target_l):
#                 cfg[i] = [labels[target_l]]
#             case ("ifgoto", _, target_l):
#                 cfg[i] = []
#                 if i + 1 < len(tac):
#                     cfg[i].append(i + 1)
#                 cfg[i].append(labels[target_l])
#             case _:
#                 cfg[i] = []
#                 if i + 1 < len(tac):
#                     cfg[i].append(i + 1)
#
#     return cfg
#

# network X - coloring algorithmus
# def basis_block(n_instructions, tac):
#     """
#     Teilt den Kontrollflussgraphen in Basisblöcke auf.
#     :param cfg: Kontrollflussgraph als Dictionary
#     :param n_instructions: Anzahl der TAC-Instruktionen
#     :return: Liste von Basisblöcken (Start-, Endindex)
#     """
#     leaders = {0}
#     labels = {}
#
#     for i, instr in enumerate(tac):
#         match instr:
#             case ("label", target_l):
#                 labels[target_l] = i
#
#     for i, instr in enumerate(tac):
#         match instr:
#             case ("goto", target_l):
#                 if i + 1 < n_instructions:
#                     leaders.add(i + 1)
#                 leaders.add(labels[target_l])
#             case ("ifgoto", _, target_l):
#                 if i + 1 < n_instructions:
#                     leaders.add(i + 1)
#                 leaders.add(labels[target_l])
#             case _:
#                 continue
#
#     leaders = sorted(leaders)
#     blocks = []
#     for i in range(len(leaders)):
#         start = leaders[i]
#         end = leaders[i + 1] if i + 1 < len(leaders) else n_instructions
#         blocks.append((start, end))
#
#     return blocks
#


# def register_coloring(cfg, tac):
#     """
#     Führt eine einfache Register-Allokation basierend auf Lebendigkeitsanalyse durch.
#     :param cfg: Kontrollflussgraph als Dictionary
#     :param tac: Liste von TAC-Anweisungen
#     :return: Mapping von Registern zu reduzierten Registern
#     """
#     in_sets, out_sets = liveness2(cfg, tac)
#     interference_graph = {}
#
#     n_instructions = infer_n_instructions(cfg)
#     for i in range(n_instructions):
#         live_vars = out_sets[i].union(in_sets[i])
#         for var1 in live_vars:
#             if var1 not in interference_graph:
#                 interference_graph[var1] = set()
#             for var2 in live_vars:
#                 if var1 != var2:
#                     interference_graph[var1].add(var2)
#
#     coloring = {}
#
#     for var in sorted(
#         interference_graph, key=lambda v: len(interference_graph[v]), reverse=True
#     ):
#         neighbor_colors = {
#             coloring.get(neigh)
#             for neigh in interference_graph[var]
#             if neigh in coloring
#         }
#         color = 0
#         while color in neighbor_colors:
#             color += 1
#         coloring[var] = color
#
#     return coloring
#
#
# def assign_regs(tac, coloring):
#     """
#     Weist den TAC-Anweisungen die zugewiesenen Register zu.
#     :param tac: Liste von TAC-Anweisungen
#     :param coloring: Mapping von Variablen zu Registern
#     :return: TAC mit zugewiesenen Registern
#     """
#     print(tac)
#     print(coloring)
#     assigned_tac = []
#
#     for instruction in tac:
#         new_instruction = []
#         for part in instruction:
#             if isinstance(part, str) and part in coloring:
#                 new_instruction.append(f"R{coloring[part]}")
#             else:
#                 new_instruction.append(part)
#         assigned_tac.append(tuple(new_instruction))
#
#     print("\nTAC mit zugewiesenen Registern:")
#     for line_no, instr in enumerate(assigned_tac):
#         print(f"{line_no:02}: {instr}")
#
#     return assigned_tac


#  --------- CONSTANT FOLDING ---------
def constant_folding(tac):
    """
    Führt Constant Folding auf dem gegebenen dreistelligen Zwischencode (TAC) durch.
    :param tac: Liste von TAC-Anweisungen
    :return: Optimierter TAC mit gefalteten Konstanten
    """
    optimized_tac = []

    for instruction in tac:
        match instruction:
            case (op, target, arg1, arg2) if op in {"+", "-", "*", "/"}:
                if isinstance(arg1, int) and isinstance(arg2, int):
                    if op == "+":
                        result = arg1 + arg2
                    elif op == "-":
                        result = arg1 - arg2
                    elif op == "*":
                        result = arg1 * arg2
                    elif op == "/":
                        result = arg1 // arg2  # Ganzzahlige Division
                    optimized_tac.append(("=", target, result))
                else:
                    optimized_tac.append(instruction)
            case _:
                optimized_tac.append(instruction)

    return optimized_tac


#  --------- COMMON SUBEXPRESSION ELIMINATION ---------
def common_subexpression_elimination(tac):
    """
    Führt Common Subexpression Elimination auf dem gegebenen dreistelligen Zwischencode (TAC) durch.
    :param tac: Liste von TAC-Anweisungen
    :return: Optimierter TAC mit eliminierten gemeinsamen Teilausdrücken
    """
    optimized_tac = []
    expr_table = {}

    for instruction in tac:
        match instruction:
            case (op, target, arg1, arg2) if op in {"+", "-", "*", "/"}:
                expr = (op, arg1, arg2)
                if expr in expr_table:
                    optimized_tac.append(("=", target, expr_table[expr]))
                else:
                    expr_table[expr] = target
                    optimized_tac.append(instruction)
            case _:
                optimized_tac.append(instruction)

    return optimized_tac


#  --------- COPY PROPAGATION ---------
def copy_propagation(tac):
    """
    Führt Copy Propagation auf dem gegebenen dreistelligen Zwischencode (TAC) durch.
    :param tac: Liste von TAC-Anweisungen
    :return: Optimierter TAC mit propagierten Kopien
    """
    optimized_tac = []
    copy_table = {}

    for instruction in tac:
        match instruction:
            case ("=", target, source):
                if source in copy_table:
                    copy_table[target] = copy_table[source]
                else:
                    copy_table[target] = source
                optimized_tac.append(instruction)
            case _:
                new_instruction = []
                for part in instruction:
                    if isinstance(part, str) and part in copy_table:
                        new_instruction.append(copy_table[part])
                    else:
                        new_instruction.append(part)
                optimized_tac.append(tuple(new_instruction))

    return optimized_tac


#  --------- DEAD CODE ELIMINATION ---------
def dead_code_elimination(tac):
    """
    Führt Dead Code Elimination auf dem gegebenen dreistelligen Zwischencode (TAC) durch.
    :param tac: Liste von TAC-Anweisungen
    :return: Optimierter TAC mit eliminiertem totem Code
    """
    optimized_tac = []
    used_vars = set()

    for instruction in reversed(tac):
        match instruction:
            case ("=", target, source):
                if target in used_vars:
                    optimized_tac.append(instruction)
                    if isinstance(source, str):
                        used_vars.add(source)
                else:
                    continue
            case (op, target, arg1, arg2) if op in {
                "+",
                "-",
                "*",
                "/",
                "<=",
                "<",
                ">=",
                ">",
                "==",
                "!=",
            }:
                if target in used_vars:
                    optimized_tac.append(instruction)
                    if isinstance(arg1, str):
                        used_vars.add(arg1)
                    if isinstance(arg2, str):
                        used_vars.add(arg2)
                else:
                    continue
            case _:
                optimized_tac.append(instruction)

    optimized_tac.reverse()
    return optimized_tac


#  --------- LOOP INVARIANT CODE MOTION ---------
def loop_invariant_code_motion(tac):
    """
    Führt Loop Invariant Code Motion auf dem gegebenen dreistelligen Zwischencode (TAC) durch.
    :param tac: Liste von TAC-Anweisungen
    :return: Optimierter TAC mit verschobenem loop-invariantem Code
    """
    optimized_tac = []
    loop_invariants = []

    in_loop = False
    for instruction in tac:
        match instruction:
            case ("label", label) if label.startswith("loop_start"):
                in_loop = True
                optimized_tac.append(instruction)
            case ("label", label) if label.startswith("loop_end"):
                in_loop = False
                optimized_tac.append(instruction)
                optimized_tac.extend(loop_invariants)
                loop_invariants.clear()
            case (op, target, arg1, arg2) if op in {"+", "-", "*", "/"}:
                if in_loop and isinstance(arg1, int) and isinstance(arg2, int):
                    loop_invariants.append(instruction)
                else:
                    optimized_tac.append(instruction)
            case _:
                optimized_tac.append(instruction)

    return optimized_tac


#  --------- STRENGTH REDUCTION ---------
def strength_reduction(tac):
    """
    Führt Strength Reduction auf dem gegebenen dreistelligen Zwischencode (TAC) durch.
    :param tac: Liste von TAC-Anweisungen
    :return: Optimierter TAC mit reduzierter Rechenstärke
    """
    optimized_tac = []

    for instruction in tac:
        match instruction:
            case ("*", target, arg1, arg2):
                if isinstance(arg2, int) and arg2 == 2:
                    optimized_tac.append(("+", target, arg1, arg1))
                else:
                    optimized_tac.append(instruction)
            case _:
                optimized_tac.append(instruction)

    return optimized_tac
