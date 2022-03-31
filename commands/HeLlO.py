COMMAND = "hello"


def func(Message, _):
    Message.fastReply(f"Hello, {Message.sender.name}")
