# ------------------- Environment -------------------#
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Entry:
    value: Any = None
    idx: int = 0
    ty: str = ""

    def __repr__(self):
        return str(tuple(self.__dict__.values()))


class SymbolTable(dict):

    def put(self, names):
        """
        Packt Jedes Element der Liste als undefiniert auf dem Environment.
        @arg names: Kann eine Liste oder Tuple sein
        @return gibt sich selber als Object aus
        """
        if isinstance(names, (list, tuple, set)):
            for name in names:
                self[name] = Entry()
        else:
            self[names] = Entry()
        return self

    def cpy(self, names):
        """
        Erstellet eine Deepcopy des Environments und packt die Namen als undefiniert darauf.
        @arg names: Kann eine Liste oder Tuple sein
        @return gibt das neue Environment als Object aus
        """
        new_env = SymbolTable()
        for k, v in self.items():
            new_env[k] = Entry(v.value, v.idx, v.ty)
        new_env.put(names)
        return new_env


# ------------------- Builtin Function -------------------#
@dataclass
class BuiltinFunction:
    name: str
    fn: Callable

    def __call__(self, pos, key, eval):
        return self.fn(pos, key, eval)


def builtin_print(pos_args, key_args=None, *_):
    """
    Gibt die Argumente auf der Konsole aus
    Example : echo(1,2,3) -> 1 2 3
    """
    kwargs = key_args or {}
    print(*pos_args, **kwargs)
    return None


def builtin_len(pos_args, *_):
    """
    Länge einer Liste wird zurückgegeben
    Example : len((1, (2, (3, None)))) == 3
    """
    if not pos_args:
        raise TypeError("len() missing 1 required positional argument")
    obj = pos_args[0]

    if isinstance(obj, tuple):
        count = 0
        cur = obj
        while isinstance(cur, tuple) and cur is not None:
            count += 1
            cur = cur[1]
            if cur is None:
                break
        return count
    return len(obj)


def builtin_list(pos_args, *_):
    """Lisp Liste wird erstellt
    Example : list(1,2,3) == (1, (2, (3, None)))
            | list(1) == (1, None)
            | list() == (None)
    """
    if not pos_args:
        return None
    node = (pos_args[-1], None)
    for v in reversed(pos_args[:-1]):
        node = (v, node)
    return node


def builtin_assert(pos_args, *_):
    """Assert a Statement
    assert(statement, erwartung)
    """
    if len(pos_args) != 2:
        raise TypeError("assert() takes exactly 2 positional arguments")
    statement = pos_args[0]
    erwartet = pos_args[1]
    assert statement == erwartet
    return int(statement == erwartet)
