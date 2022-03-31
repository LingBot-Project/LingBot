COMMAND = "hello"


def func(Message):
    Message.fastReply(f"Hello, {Message.sender.name}")
