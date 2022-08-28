from events.Events import *
from module.modules.IModule import IModule
import utils.Message as Message
import time

feed_back_cooldown = {}


class Feedback(IModule):
    def process(self, event: Event) -> None:
        if isinstance(event, GroupMessageEvent):
            global feed_back_cooldown
            if event.get_commands()[0] != "!feedback":
                return
            sender = feed_back_cooldown.get(event.get_message().sender.id)
            cd = feed_back_cooldown.get(sender)
            cur_time = time.time()
            if cd is not None:
                if cd > cur_time:
                    event.reply("抱歉, 但是反馈功能还在冷却中")
                    return
                # end if
            # end if
            if len(event.get_commands()) < 2:
                event.reply("这里貌似没有任何东西呢 = =")
                return
            # end if
            feed_back_cooldown[sender] = cur_time + 300
            Message.sendMessage(f"用户 {sender}() 提交了反馈: \n{event.get_message().text[10:]}", target_group=Message.DEV_GROUP)
            event.reply("提交成功! ")
        # end if
    # end def
# end class
