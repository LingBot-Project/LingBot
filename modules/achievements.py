import re

from utils.qqbot import sendMessage


def on_message(msg, command_list):
    if command_list[0] in ["!achievements", "!成就"]:
        if command_list[1] == "help":
            sendMessage("""成就指令 : !achievements/!成就
    列出自己的成就 : !achievements/!成就 list me
    列出他人的成就 : !achievements/!成就 list <QQ|@>
    清空自己的成就 : !achievements/!成就 empty
    成就大全 : 这要你自己探索了""", target_group=msg.group.id)
        if command_list[1] == "list":
            acmsg = ""
            if command_list[2] == "me":
                for aclist in ACCOMPLISHMENT["qq"][str(msg.sender.id)]:
                    acmsg += f'[CQ:image,file={ACCOMPLISHMENT["ACCOMPLISHMENT"][aclist]}]'
                msg.fast_reply("您获得的成就有\n" + acmsg)
            else:
                atcq = re.search(r'\[CQ:at,qq=(.*)]', msg.text)
                if atcq is not None:
                    command_list = msg.text.replace("[CQ:at,qq={}]".format(atcq.group(1)), str(atcq.group(1))).split(
                        " ")
                if command_list[2] not in ACCOMPLISHMENT["qq"] or len(ACCOMPLISHMENT["qq"][command_list[2]]) == 0:
                    msg.fast_reply(
                        f"{f'[CQ:at,qq={command_list[2]}]' if atcq is not None else command_list[2]}还未获得任何成就")
                    return
                for aclist in ACCOMPLISHMENT["qq"][command_list[2]]:
                    acmsg += f'[CQ:image,file={ACCOMPLISHMENT["ACCOMPLISHMENT"][aclist]}]'
                msg.fast_reply(
                    f"{f'[CQ:at,qq={command_list[2]}]' if atcq is not None else command_list[2]}获得的成就有\n{acmsg}")
        elif command_list[1] == "empty":
            ACCOMPLISHMENT["qq"][str(msg.sender.id)] = []
            msg.fast_reply("已清空您的成就")

    if re.search(r"我是傻逼|我是傻子|i am stupid|i'm stupid|i'm a fool|i‘m an idiot|i am a fool|i am an idiot", msg.text):
        if str(msg.sender.id) not in ACCOMPLISHMENT["qq"]:
            ACCOMPLISHMENT["qq"][str(msg.sender.id)] = []
            get_achievements(msg.sender.id, msg, "i_m_stupid")
        if "i_m_stupid" not in ACCOMPLISHMENT["qq"][str(msg.sender.id)]:
            get_achievements(msg.sender.id, msg, "i_m_stupid")


def get_achievements(qq, msg, achievements):
    ACCOMPLISHMENT["qq"][str(qq)].append(achievements)
    msg.fast_reply(f'恭喜你获得了一个成就！！\n[CQ:image,file={ACCOMPLISHMENT["ACCOMPLISHMENT"][achievements]}]')


def get_achievement_image(block, title, string1, string2=None):
    title = title.replace(" ", "..")
    string1 = string1.replace(" ", "..")
    if string2 is not None:
        string2 = string2.replace(" ", "..")
    return f'https://minecraft-api.com/api/achivements/{block}/{title}/{string1}/{string2 if string2 is not None else ""}'


ACCOMPLISHMENT = {"qq": {}, "ACCOMPLISHMENT": {
    "i_m_stupid": get_achievement_image("sand", "STUPID", "I am stupid")
}}