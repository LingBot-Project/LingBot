from events.Events import *
from module.modules.IModule import IModule
import utils.Message as Message
import time
import uuid

feed_back_cooldown = {}
fb_help = """指令用法: !feedback <str>
在提交反馈之前, 请先确定您要干什么

提交 bug/报错?
附上对应报错图片
如果可以, 请对该行为简要的说明(如何发生, 等)

提交 意见/建议?
增加新功能:
这是个什么类型功能?
这个功能能干什么?
请尽量把各种信息详细地描述 如果这个功能来自于其他开源项目, 请附上github链接

在反馈提交成功之后, 你将会收到一个反馈码(uuid4格式) 如果您是认真提交的反馈则请妥善保管(忙得要死也不一定每个都能顾得上 =_=, 但能看到一定会看的)
"""


class Feedback(IModule):
    def process(self, event: Event) -> None:
        if isinstance(event, GroupMessageEvent):
            global feed_back_cooldown
            if event.get_commands()[0] != "!feedback":
                return
            # end if
            if len(event.get_commands()) < 2:
                event.reply(fb_help)
                return
            # end if
            sender = event.get_message().sender
            cd = feed_back_cooldown.get(sender.id)
            cur_time = time.time()
            if cd is not None:
                if cd > cur_time:
                    event.reply("抱歉, 但是您的反馈还在冷却中")
                    return
                # end if
            # end if
            fb_id = str(uuid.uuid4())
            feed_back_cooldown[sender.id] = cur_time + 300
            Message.sendMessage(f"用户 {sender} 提交了反馈({event.get_message().group.id}, {event.get_message().id}, {fb_id}): \n{event.get_message().text[10:]}", target_group=Message.DEV_GROUP)
            event.reply(f"提交成功! 您的反馈编号为{fb_id}")
        # end if
    # end def
# end class
