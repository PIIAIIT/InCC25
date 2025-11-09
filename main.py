import sys
from parser import parser, print_ast

from environment import SymbolTable
from interpreter import eval
from typisierung import typecheck
from lexer import print_traceback
from zwischencode import code_c, code_b, free
from optimierung import (
    control_flow,
    basis_block,
    infer_n_instructions,
    liveness,
    register_coloring,
)
import ice2_ws25.ice_machine as ice_machine
import readline

COLORS = {
    "r": "\001\033[31m\002",
    "g": "\001\033[32m\002",
    "b": "\001\033[34m\002",
    "_": "\001\033[0m\002",
}

ENV = SymbolTable()


def prod(src, debug=False, write=False, filename="iic_code.iic", iic=False, config={}):
    if config != {}:
        debug = config["debug"]
        write = config["write"]["b_write"]
        filename = config["write"]["file"]
        iic = config["iic"]
    # Parser
    result = parser.parse(src, debug=debug)
    # Typecheck und Symboltabelle
    result = typecheck(result, ENV)
    # print_ast(result)
    # Free Variables
    free(result)

    end_result = eval(result, ENV)
    inter_result = []
    regs = {}

    if iic:
        # Intermediate Code
        inter_result = code_c(result, dict(), "R0", set(), code_b)

        if write:
            write_iic(inter_result, filename)

        # # Check with ice_machine
        regs = ice_machine.run(inter_result, debug=True, detailed=True)

    # Optimization
    if config.get("optimize", False):
        print("Optimizing...")
        cfg = control_flow(inter_result)
        # bloecke = basis_block(infer_n_instructions(cfg), inter_result)
        in_sets, out_sets = liveness(cfg, inter_result)
        print("Liveness Analysis:")
        for i in range(len(inter_result)):
            print(
                f"Instr {i}: IN = {in_sets[i]}, OUT = {out_sets[i]} | {inter_result[i]}"
            )
        coloring = register_coloring(cfg, inter_result)
        print("Register Coloring:", coloring)
    #
    #
    # Print Result
    #
    for line in inter_result:
        print(COLORS["b"] + str(line) + COLORS["_"])
    print(regs) if iic else ""
    print(COLORS["b"] + str(result.ty), end=": ")
    print(COLORS["b"] + str(end_result) + COLORS["_"])


def test_code(debug=False, write={}, read={}, config={}):
    # load config
    write_file = write["file"] if len(write) > 1 else "iic_code.iic"
    write = write["b_write"] if len(write) > 0 else False

    read_file = read["file"] if len(read) > 1 else ""
    read = read["b_read"] if len(read) > 0 else False

    if config != {}:
        debug = config["debug"]
        write_file = config["write"]["file"]
        write = config["write"]["b_write"]
        read_file = config["read"]["file"]
        read = config["read"]["b_read"]

    open(write_file, "w").close() if write else None  # clean file
    while not read:
        try:
            # Eingabe lesen
            src = input(COLORS["g"] + ">>> " + COLORS["_"])
            multiline = src.strip().endswith("->") or src.count("{") > src.count("}")
            while multiline:
                tmp = input(COLORS["g"] + "... " + COLORS["_"])
                src += "\n" + tmp  # Zeilen umbrechen
                # Update multiline-Status
                multiline = src.strip().endswith("->") or src.count("{") > src.count(
                    "}"
                )

            prod(src, config=config)
        except EOFError:
            exit()
        except Exception as e:
            print(
                COLORS["r"]
                + str(print_traceback(src, result, silent=True) if debug else e)
                + COLORS["_"]
            )
        except KeyboardInterrupt as e:
            print(e)
    else:
        with open(read_file, "r") as f:
            src = f.read()
            try:
                prod(src, config=config)
                print("Execution finished.")
            except Exception as e:
                print(
                    COLORS["r"]
                    + str(print_traceback(src, result, silent=True) if debug else e)
                    + COLORS["_"]
                )


def write_iic(code, filename="iic_code.iic"):
    with open(filename, "a") as f:
        for t in code:
            f.write(ice_machine.tuple_to_infix(t))
            f.write("\n")


if __name__ == "__main__":
    config = {
        "debug": False,
        "write": {"b_write": False, "file": "iic_code.iic"},
        "read": {"b_read": False, "file": ""},
        "iic": False,
        "optimize:": False,
    }

    for eachArg in sys.argv:
        match eachArg:
            case "-debug":
                config["debug"] = True
            case "-w" | "--write":
                config["write"]["b_write"] = True
                w_filename = sys.argv[sys.argv.index(eachArg) + 1]
                config["write"]["file"] = w_filename
            case "-iic":
                config["iic"] = True
            case "-r" | "--read":
                config["read"]["b_read"] = True
                r_filename = sys.argv[sys.argv.index(eachArg) + 1]
                config["read"]["file"] = r_filename
            case "-O" | "--optimize":
                config["optimize"] = True
            case _:
                continue

    test_code(config=config)
