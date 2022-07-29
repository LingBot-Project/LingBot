from events.Events import *
from module.modules.IModule import IModule


class TestHello(IModule):
    @staticmethod
    def on_msg(event: GroupMessageEvent):
        if event.get_message().text == "!hey bot":
            event.reply(f"hey! {event.get_message().sender.name}")

    def process(self, event: Event) -> None:
        if isinstance(event, GroupMessageEvent):
            TestHello.on_msg(event)
