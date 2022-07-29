import main


class Event:
    def __init__(self): ...


class CancelableEvent(Event):
    def __init__(self):
        super().__init__()
        self._canceled: bool = False

    def is_canceled(self) -> bool:
        return self._canceled

    def cancel_event(self):
        self._canceled = True


class GroupMessageEvent(CancelableEvent):
    def __init__(self, message: main.Message):
        super().__init__()
        self._message = message

    def get_message(self):
        return self._message

    def reply(self, message: str, at: bool = True, reply: bool = True):
        self._message.fast_reply(message, at, reply)
