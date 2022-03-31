import os


class DuplicateNameException(Exception):
    pass

class ModuleManager:
    def __init__(self) -> None:
        self.func_dist = {}

    def module(self, func, name) -> function:
        if name in self.func_dist:
            raise DuplicateNameException()
        
        if name is not str:
            raise TypeError()
        
        self.func_dist[name] = func

        return func
    
    def load(self):
        self.func_dist.clear()
        for i in os.listdir(os.path.join('.', 'plugins')):
            if os.path.splitext(i)[1] == ".py":
                with open(i, 'r') as f:
                    exec(f.read())


if __name__ == "__main__":
    print("This is a Python library and shouldn't be run directly.")