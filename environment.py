from _builtin import *


class Environment(dict):
    def __init__(self, parent=None):
        self.parent = parent
        self.vars = {}

    def put(self, names: list | tuple | set):
        """
        Packt Jedes Element der Liste als undefiniert auf dem Environment.
        @arg names: Kann eine Liste oder Tuple sein
        @return gibt sich selber als Object aus
        """
        for name in names:
            if name not in self.vars:
                self.vars[name] = None
        return self

    def copy(self):
        """
        Erstellt eine neue copy des selben Environments.
        @return Seine eigene Kopie
        """
        new_env = Environment(parent=self.parent)
        new_env.vars = self.vars.copy()
        return new_env

    def define(self, name, value):
        """
        Definiert eine Variablen auf dem Environment.
        @arg name: Name der Variable
        @arg value: Wert der Variable
        """
        assert name is not None
        assert value is not None
        self.__setitem__(name, value)

    def builtins(self):
        """
        Definiert eine Variablen auf dem Environment.
        @arg name: Name der Variable
        @arg value: Wert der Variable
        """
        builtins = {
            "echo": BuiltinFunction(builtin_print),
            "länge": BuiltinFunction(builtin_len),
            "list": BuiltinFunction(builtin_list),
            "type": BuiltinFunction(lambda pos, key: type(pos[0]))
        }

        for name, fn in builtins.items():
            self[name] = fn

    def __contains__(self, name):
        if name in self.vars:
            return True
        elif self.parent is None:
            return False
        else:
            return name in self.parent

    def __getitem__(self, name):
        if name in self.vars:
            return self.vars[name]
        elif self.parent is None:
            raise KeyError(name)
        else:
            return self.parent[name]

    def __setitem__(self, name, value):
        if name in self.vars:
            self.vars[name] = value
        elif self.parent is None:
            self.vars[name] = value
        else:
            self.parent[name] = value

    def __str__(self):
        return str(self.vars) + "\n" + str(self.parent) if self.parent is not None else ""
