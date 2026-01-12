# ------------------- Environment -------------------#
from dataclasses import dataclass
from typing import Any, Optional, Callable


@dataclass
class Entry:
    value: Any = None
    idx: int = 0
    ty: str = ""

    def __repr__(self):
        return str(self.__dict__)


class SymbolTable:
    def __init__(self, parent: Optional["SymbolTable"] = None):
        self.parent = parent
        self.vars: dict[str, Entry] = {}

    def push(self, names: list | str):
        """
        Erstellt ein neues Environment mit dem aktuellen als Parent.
        @arg names: Kann eine Liste oder Tuple sein
        @return gibt das neue Environment als Object aus
        """
        return SymbolTable(self).put(names)

    def put(self, names):
        """
        Packt Jedes Element der Liste als undefiniert auf dem Environment.
        @arg names: Kann eine Liste oder Tuple sein
        @return gibt sich selber als Object aus
        """
        if not isinstance(names, (list, tuple, set)):
            names = [names]
        for name in names:
            self.vars.setdefault(name, Entry())
        return self

    def copy(self, item=None):
        """
        Erstellt eine neue copy des gleichen Environments.
        @return Seine eigene Kopie
        """
        new_env = SymbolTable(self.parent)
        new_env.vars = self.vars.copy()
        if item:
            new_env.put(item)
        return new_env

    def define(self, name, value):
        """
        Definiert eine Variablen auf dem Environment.
        @arg name: Name der Variable
        @arg value: Wert der Variable
        """
        self.put(name)
        self[name].value = value
        return self

    def builtins(self):
        """
        Definiert eine Variablen auf dem Environment.
        @arg name: Name der Variable
        @arg value: Wert der Variable
        """
        builtins = {
            "echo": builtin_print,
            "länge": builtin_len,
            "list": builtin_list,
            "assert": builtin_assert,
        }
        for name, fn in builtins.items():
            self.define(name, BuiltinFunction(name, fn))

    def clear(self):
        self.parent = None
        self.vars = {}
        self.builtins()

    def __contains__(self, name):
        return name in self.vars or (self.parent is not None and name in self.parent)

    def __getitem__(self, name) -> Entry:
        if name in self.vars:
            return self.vars[name]
        if self.parent is not None:
            return self.parent[name]
        raise KeyError(name)

    def __setitem__(self, name, value):
        if name in self.vars:
            self.vars[name] = value
            return
        if self.parent is not None and name in self.parent:
            self.parent[name] = value
            return
        raise KeyError(name)

    def __delitem__(self, name):
        if name in self.vars:
            del self.vars[name]
            return
        if self.parent is not None:
            del self.parent[name]
            return
        raise KeyError(name)

    def __str__(self):
        s = str(self.vars)
        if self.parent:
            s += "\n" + str(self.parent)
        return s

    def __repr__(self):
        return self.__str__()


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
