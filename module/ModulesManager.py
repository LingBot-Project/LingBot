from module.modules.IModule import IModule
from modules import *


# TODO
class ModuleManager:
    def __init__(self):
        self._modules = []
        pass

    def register_modules(self, *modules: IModule):
        for module in modules:
            self.register_module(module)
        pass

    def register_module(self, module: IModule):
        self._modules.append(module)
        pass

    def process_event(self, event):
        for module in self._modules:
            module.process(event)
