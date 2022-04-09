import random
import re
import time

import requests
from mcstatus import MinecraftServer

from utils import tcping
from utils.image import text2image
from utils.qqbot import get_runtime, sendMessage, getGroups, mutePerson, mute_type, search_user, unmutePerson, goodmor

SCREENSHOT_CD = 0
MC_MOTD_COLORFUL = re.compile(r"§.")

if __name__ == '__main__':
    pass


def on_message(msg, command_list):
    global SCREENSHOT_CD, ALL_MESSAGE, timePreMessage, ALL_AD, REPEATER, ADMIN_LIST, BLACK_LIST, IGNORE_GROUP, ANTISPAMMER, SPAM2_VL
    if msg.text in ["!test", "凌状态"]:
        msg.fast_reply(
            "Hello! 已处理 {} 条消息\n已经运行了 {}\n平均每条消息耗时 {} 秒\n拦截了 {} 条广告 占全部处理消息的 {}%".format(
                ALL_MESSAGE,
                get_runtime(),
                timePreMessage,
                ALL_AD,
                (ALL_AD / ALL_MESSAGE) * 100
            )
        )

    if command_list[0] == "!testchrome" and msg.sender.id == 1584784496:
        msg.fast_reply("Trying...")
        msg.fast_reply("[CQ:image,file=base64://{}]".format(
            requests.post(url="http://localhost:25666/url2base64",
                          data={"url": " ".join(command_list[1:])}).text.replace("\n", "")))

    if msg.text == "!testzb":
        if SCREENSHOT_CD + 60 <= time.time():
            msg.fast_reply("Trying...")
            goodmor(msg.group.id)
            SCREENSHOT_CD = time.time()
        else:
            msg.fast_reply("Too fast!")

    if command_list[0] == "!repeater":
        if msg.sender.isadmin():
            if command_list[1] == "add":
                if (msg.group.id, int(command_list[2])) in REPEATER:
                    msg.fast_reply("复读机名单内已经有这个人了")
                    return
                REPEATER.append((msg.group.id, int(command_list[2])))
                msg.fast_reply("操作成功")
            elif command_list[1] == "remove":
                if (msg.group.id, int(command_list[2])) not in REPEATER:
                    msg.fast_reply("复读机名单内没有这个人")
                    return
                REPEATER.remove((msg.group.id, int(command_list[2])))
                msg.fast_reply("操作成功")

    if command_list[0] == "!tcping":
        if len(command_list) == 1:
            msg.fast_reply("语法错误 使用方法为: !tcping IP[:端口(默认为80)]\n如: !tcping api.github.com:80")
        else:
            msg.fast_reply("正在进行TCPing")
            _host = ""
            _port = "80"
            if command_list[1].find(":") != -1:
                _host, _port = command_list[1].split(":")
            else:
                _host = command_list[1]

            _ping = tcping.Ping(_host, int(_port), 1.0)
            _ping.ping(5)
            msg.fast_reply("[CQ:image,file=base64://{}]".format(text2image(_ping.result.raw.replace(", ", "\n"))))

    if command_list[0] == "!admin":
        if command_list[1] == "list":
            msg.fast_reply(", ".join('%s' % _id for _id in ADMIN_LIST))
        elif not msg.sender.isadmin():
            msg.fast_reply("你的权限不足!")
            return
        if command_list[1] == "add":
            if int(command_list[2]) in ADMIN_LIST:
                msg.fast_reply("超管内已经有这个人了")
                return
            ADMIN_LIST.append(int(command_list[2]))
            msg.fast_reply("操作成功")
        elif command_list[1] == "remove":
            if int(command_list[2]) not in ADMIN_LIST:
                msg.fast_reply("超管内没有这个人")
                return
            elif int(command_list[2]) == 1584784496:
                msg.fast_reply("不可以这么干哟~~")
                sendMessage("{}尝试把您(Owner)从超管列表删除".format(msg.sender.id), target_group=963024167)
                return
            ADMIN_LIST.remove(int(command_list[2]))
            msg.fast_reply("操作成功")

    if command_list[0] == "!blacklist":
        if command_list[1] == "list":
            msg.fast_reply(", ".join('%s' % id for id in BLACK_LIST))
        elif not msg.sender.isadmin():
            msg.fast_reply("你的权限不足!")
            return
        if command_list[1] == "add":
            if int(command_list[2]) in BLACK_LIST:
                msg.fast_reply("黑名单内已经有这个人了")
                return
            elif int(command_list[2]) == 1584784496:
                msg.fast_reply("不可以这么干哦~~")
                sendMessage("{}尝试把您(Owner)添加进黑名单".format(msg.sender.id), target_group=963024167)
                return
            BLACK_LIST.append(int(command_list[2]))
            msg.fast_reply("操作成功")
        elif command_list[1] == "remove":
            if int(command_list[2]) not in BLACK_LIST:
                msg.fast_reply("黑名单内没有这个人")
                return
            BLACK_LIST.remove(int(command_list[2]))
            msg.fast_reply("操作成功")

    if command_list[0] == "/mcping":
        server = MinecraftServer.lookup(command_list[1]).status()
        aaa = "Motd:\n{0}\n在线人数:{1}/{2}\nPing:{3}\nVersion:{4} (protocol:{5})".format(
            re.sub(MC_MOTD_COLORFUL, "", server.description),
            server.players.online,
            server.players.max,
            server.latency,
            re.sub(MC_MOTD_COLORFUL, "", server.version.name),
            server.version.protocol
        )
        aaa = aaa.replace("Hypixel Network", "嘉心糖 Network")
        aaa = "[CQ:image,file=base64://{}]".format(text2image(aaa))
        if server.favicon is not None:
            aaa = aaa + "\n[CQ:image,file=" + server.favicon.replace("data:image/png;base64,", "base64://") + "]"
        msg.fast_reply(aaa)

    if command_list[0] == "!send":
        if msg.sender.isadmin():
            msg1 = " ".join(command_list[2:])
            if command_list[1] == "all":
                s = getGroups()
                msg.fast_reply("正在群发... 目标:{}个群".format(len(s)))
                _prefix = "(由 {}({}) 发起的群发消息)".format(msg.sender.name, msg.sender.id)
                for i in s:
                    if i not in IGNORE_GROUP:
                        sendMessage(_prefix + msg1, target_group=i)
                        time.sleep(random.randint(1500, 1900) / 1000)
                msg.fast_reply("群发完成")
            else:
                sendMessage(msg1, target_group=command_list[1])
        else:
            msg.fast_reply("你的权限不足!")

    if command_list[0] == "!mute":
        if msg.sender.isadmin():
            atcq = re.search(r'\[CQ:at,qq=(.*)]', msg.text)
            if atcq is not None:
                command_list = msg.text.replace("[CQ:at,qq={}]".format(atcq.group(1)), str(atcq.group(1))).split(
                    " ")
            if command_list[1] == "this":
                command_list[1] = msg.group.id
            else:
                command_list[1] = int(command_list[1])
            command_list[2] = int(command_list[2].replace("@", ""))
            command_list[3] = int(command_list[3])
            if command_list[3] == 0:
                unmutePerson(command_list[1], command_list[2])
            else:
                mute_time = command_list[3] * 60
                time_type = 'min'
                if len(command_list) > 4:
                    if command_list[4] == 's' or command_list[4] == '秒':
                        time_type = 's'
                        mute_time = command_list[3]
                    if command_list[4] == 'h' or command_list[4] == '小时':
                        time_type = 'h'
                        mute_time = command_list[3] * 3600
                    if command_list[4] == 'd' or command_list[4] == '天':
                        time_type = 'd'
                        mute_time = command_list[3] * 86400

                mutePerson(command_list[1], command_list[2], mute_time)
                msg.fast_reply(
                    f"已尝试在群 {command_list[1]} 禁言 {command_list[2]} {command_list[3]}{mute_type(time_type)}")
        else:
            msg.fast_reply("你的权限不足!")

    if command_list[0] == "!vl":
        if not msg.sender.isadmin():
            msg.fast_reply("你的权限不足!")
            return
        if command_list[1] == "spam2":
            msg.fast_reply(f'此人spam2 vl为: {SPAM2_VL[int(command_list[2])]}')
            return
        elif command_list[1] == "spam":
            msg.fast_reply(f"此群成员spam vl为: {int(ANTISPAMMER[command_list[2]])}")
            return

    if command_list[0] == "!namelocker":
        msg.fast_reply("恭喜你找到了一个彩蛋!")
        # 鬼!
        return

    if command_list[0] == "!search":
        if not msg.sender.isadmin():
            msg.fast_reply("你的权限不足!")
            return
        msg.fast_reply("正在从机器人所有加入的群搜索此人")
        a = search_user(int(command_list[1]))
        msg.fast_reply("搜索完成:\n{}".format(a))