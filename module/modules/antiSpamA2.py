from events.Events import *
from module.modules.IModule import IModule
from utils.EvictingList import EvictingList


TIME_SAMPLES = {}


def on_msg(event: GroupMessageEvent):
    pass  # TODO


class AntiSpam(IModule):
    def process(self, event: Event) -> None:
        if isinstance(event, GroupMessageEvent):
            on_msg(event)
