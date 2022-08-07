#import main as _instance
class Event:
    def __init__(self): ...


class CancelableEvent(Event):
    def __init__(self):
        super().__init__()
        self.canceled: bool = False

    def is_canceled(self) -> bool:
        return self.canceled

    def cancel_event(self):
        self.canceled = True


class GroupMessageEvent(CancelableEvent):
    # def __init__(self, message: _instance.Message):
    def __init__(self, message):
        super().__init__()
        self._message = message
        self.command_list = message.text.split(" ")

    def get_message(self):
        return self._message

    def reply(self, message: str, at: bool = True, reply: bool = True):
        self._message.fast_reply(message, at, reply)
