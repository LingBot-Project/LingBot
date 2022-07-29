from events.Events import *
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

    def process_event(self, event: Event) -> bool:
        for module in self._modules:
            module.process(event)

        if isinstance(event, CancelableEvent):
            return event.is_canceled()
        return False
