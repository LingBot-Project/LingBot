from events.Events import *
from module.modules.IModule import IModule


class HelloNew(IModule):
    @staticmethod
    def on_message(event: GroupMessageEvent):
        if event.get_message().text == "hello ling bot!":
            event.reply(f"hello~ {event.get_message().sender.name}")

    def process(self, event: Event) -> None:
        if isinstance(event, GroupMessageEvent):
            HelloNew.on_message(event)
