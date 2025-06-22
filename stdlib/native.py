import math


def native_sqrt(args):
    return math.sqrt(args[0])


def native_pow(args):
    return math.pow(args[0], args[1])


def native_str_len(args):
    return len(args[0])


def native_len(args):
    return len(args[0])


def native_str_split(args):
    return args[0].split(args[1])


def native_error(args):
    raise Exception(f"Runtime error: {args[0]}")


def native_abs(args):
    return math.fabs(args[0])
