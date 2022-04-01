# -*- coding: UTF-8 -*-
import inspect
import os


class DuplicateNameException(Exception):
    pass

class ModuleManager:
    def __init__(self):
        self.func_dist = {}

    def register_module(self, func, name) -> None:
        self.func_dist[name] = func
    
    def load(self) -> None:
        self.func_dist.clear()
        for i in os.listdir(os.path.join('.', 'plugins')):
            if os.path.splitext(i)[1] == ".py":
                with open(os.path.join('.', 'plugins', i), 'rb') as f:
                    exec(f.read().decode('utf-8').replace("main.Modules", "self"))


if __name__ == "__main__":
    print("This is a Python library and shouldn't be run directly.")