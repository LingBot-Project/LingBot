# -*- coding: UTF-8 -*-
import os


class DuplicateNameException(Exception):
    pass

class ModuleManager:
    def __init__(self) -> None:
        self.func_dist = {}

    def register_module(self, func, name):
        self.func_dist[name] = func
    
    def load(self) -> None:
        self.func_dist.clear()
        for i in os.listdir(os.path.join('.', 'plugins')):
            if os.path.splitext(i)[1] == ".py":
                exec("import plugins."+os.path.splitext(i)[0])


if __name__ == "__main__":
    print("This is a Python library and shouldn't be run directly.")