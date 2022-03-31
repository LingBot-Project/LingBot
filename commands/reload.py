COMMAND = "!reload"


def func(Message):
    if Message.sender.isadmin():
        Message.fastReply("正在尝试这么做...")
        # TODO 做个der
