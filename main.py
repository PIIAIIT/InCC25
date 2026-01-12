from parser import parser, print_ast
import os
import argparse
from argparse import Namespace

from environment2 import SymbolTable
from interpreter import eval
from typisierung import typecheck, mksymtabs
from zwischencode import free, iic_gen, write_iic
from optimierung import optimize
import subprocess
import ice2_ws25.ice_machine as ice_machine
from maschinecode import maschine_code, write_to_file
import readline

COLORS = {
    "r": "\001\033[31m\002",
    "g": "\001\033[32m\002",
    "b": "\001\033[34m\002",
    "_": "\001\033[0m\002",
}


def prod(src, config: Namespace):
    # Parser
    result = parser.parse(src)
    print("Parsed successfully.") if config.debug else None

    # Typecheck und Symboltabelle
    mksymtabs(result, SymbolTable())
    # print_ast(result)
    typecheck(result)
    print("Typechecked successfully.") if config.debug else None

    # Free Variables
    free(result)
    print("Free variables computed.") if config.debug else None

    # Interpreter
    end_result = eval(result, SymbolTable())
    print("Interpreted successfully.") if config.debug else None

    # Zwischencode Generation
    inter_result = []
    regs = {}

    # Intermediate Code
    if config.iic:
        inter_result = iic_gen(result, debug=config.debug)
        print("Intermediate code generated.") if config.debug else None

        if config.iic:
            write_iic(inter_result, config.iic)
            print(f"IIC written to {config.iic}.") if config.debug else None

        regs = ice_machine.run(
            inter_result,
            debug=config.debug or config.detailed,
            detailed=config.detailed,
        )
        print("IIC executed successfully.") if config.debug else None

    # Optimization
    if config.optimize or config.Ov:
        if not inter_result:
            raise Exception("Intermediate code must be generated before optimization.")

        inter_result = optimize(inter_result, visual=config.visual, debug=config.debug)

        # Verify correctness after optimization
        regs2 = ice_machine.run(inter_result, debug=config.debug, detailed=config.debug)
        if regs != regs2:
            (
                print(
                    COLORS["r"]
                    + "Warning: Register states differ after optimization!"
                    + COLORS["_"]
                )
                if config.debug
                else None
            )
            print(COLORS["b"] + str(regs) + COLORS["_"]) if config.debug else None
            print(COLORS["g"] + str(regs2) + COLORS["_"]) if config.debug else None
        else:
            print("Optimization verified successfully.") if config.debug else None
        (
            write_iic(inter_result, "_optimized.".join(config.iic.split(".")))
            if config.iic
            else None
        )

    if config.asm:
        asm_result = maschine_code(inter_result, config.C)
        print("Machine code generated.") if config.debug else None

        if config.debug:
            for line in asm_result:
                print(line)

        write_to_file(asm_result, config.asm)
        print(f"ASM written to {config.asm}.") if config.debug else None

    # Compile to executable
    if config.compile:
        subprocess.run(
            ["nasm", "-f", "elf64", "-o", "main.o", config.asm, "-g", "-F", "dwarf"]
        )
        subprocess.run(
            [
                "gcc",
                "-gdwarf",
                "-ggdb",
                "-g",
                "-z",
                "noexecstack",
                "-no-pie",
                "-o",
                "main",
                "-L",
                "libICE",
                "main.o",
            ]
            + (["-lICE", "-static"] if config.C else ["-lICE"])
        )
        print("Compiled to executable 'main'.")

    #
    # Print Result
    #

    # print(COLORS["b"] + str("\n".join(map(str, inter_result))) + COLORS["_"])
    print(COLORS["b"] + str(result.ty), end=": ")
    print(
        COLORS["g"] + str(end_result) + COLORS["_"]
        if regs["R0"] == end_result
        else (
            COLORS["r"]
            + str(regs)
            + COLORS["_"]
            + ", Real result: "
            + COLORS["b"]
            + str(end_result)
            + COLORS["_"]
            if config.debug
            else COLORS["b"] + str(end_result) + COLORS["_"]
        )
    )


def test_code(config: Namespace):
    while not config.read:  # interactive mode
        histfile = os.path.join(os.path.expanduser("~"), ".iic_history")
        readline.read_history_file(histfile) if os.path.exists(histfile) else None
        readline.set_history_length(1000)
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
            print(COLORS["r"] + str(e) + COLORS["_"])
        except KeyboardInterrupt as e:
            print(e)
    else:
        with open(config.read, "r") as f:
            src = f.read()
            try:
                prod(src, config=config)
                print("Execution finished.")
            except Exception as e:
                print(COLORS["r"] + str(e) + COLORS["_"])


if __name__ == "__main__":
    cli = argparse.ArgumentParser()  # just to enable -h/--help
    cli.add_argument("filename", nargs="?", help="Source code file to execute")
    cli.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    cli.add_argument(
        "-D", "--detailed", action="store_true", help="Enable detailed debug mode"
    )
    cli.add_argument("-r", "--read", metavar="file", help="Read source code from file")
    cli.add_argument(
        "-iic",
        nargs="?",
        const=True,
        default="iic_code.iic",
        metavar="file",
        help="Generate and execute intermediate code",
    )
    cli.add_argument(
        "-asm",
        nargs="?",
        const=True,
        default="main.asm",
        metavar="file",
        help="Generate assembly code and write to file",
    )
    cli.add_argument(
        "-c",
        "--compile",
        action="store_true",
        help="Compile the assembly code to an executable",
    )
    cli.add_argument("-C", action="store_true", help="Compile with ICELib")
    cli.add_argument(
        "-O", "--optimize", action="store_true", help="Optimize the intermediate code"
    )
    cli.add_argument(
        "-Ov",
        action="store_true",
        help="Optimize the intermediate code with visualization",
    )
    cli.add_argument(
        "-v",
        "--visual",
        action="store_true",
        help="Enable visualization for optimization",
    )
    args = cli.parse_args()

    test_code(config=args)
