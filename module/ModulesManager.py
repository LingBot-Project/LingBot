from events.Events import *
from module.modules.IModule import IModule
from module.modules import HelloNew, TestHello
from typing import List


class ModuleManager:
    def __init__(self):
        self._modules: List[IModule] = []
        self.register_modules(
            HelloNew.HelloNew(),
            TestHello.TestHello()
        )
        pass

    def register_modules(self, *modules: IModule):
        for module in modules:
            if isinstance(module, IModule):
                self.register_module(module)

    def register_module(self, module: IModule):
        self._modules.append(module)

    def process_event(self, event: Event) -> bool:
        for module in self._modules:
            module.process(event)

        if isinstance(event, CancelableEvent):
            return event.is_canceled()
        return False
