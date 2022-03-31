# -*- coding: UTF-8 -*-
from ast import Mod
import configparser
import base64
import datetime
import json
import random
import re
import threading
import time
import traceback
import hypixel
import psutil
import tcping
from io import BytesIO

import requests
import websocket
from mcstatus import MinecraftServer
from PIL import Image, ImageDraw, ImageFont
from apscheduler.schedulers.blocking import BlockingScheduler
from moduleManager import *

hypixel.setKeys(["69a1e20d-94ba-4322-91c5-003c6a5dd271"])
hypixel.setCacheTime(30.0)

SERVER_ADDR = "127.0.0.1"
ADMIN_LIST = [1790194105, 1584784496, 2734583, 2908331301, 3040438566,1474002938]
HYPBAN_COOKIE = None
SEND_AD_LIST = {}
BLACK_LIST = []
CACHE_MESSAGE = []
BANCHECK_UID = {}
WSURL = SERVER_ADDR + ":10540"
HTTPURL = SERVER_ADDR + ":10500"
MC_MOTD_COLORFUL = re.compile(r"§.")
ALL_MESSAGE = 0
MESSAGE_PRE_MINUTE = [0, 0]
ALL_AD = 0
BILI_BV_RE = re.compile(r"BV([a-zA-Z0-9]{10})")
REQ_TEXT = re.compile(r"get±.*±")
timePreMessage = 0
recordTime = int(time.time())
isChatBypassOpened = False
ANTISPAMMER = {}
IGNORE_GROUP = [1079822858]
FEEDBACKS = {}
REPEATER = []
ANTI_AD = r"定制水影|加群(:)[0-9]{5,10}|.*内部|\n元|破甲|天花板|工具箱|绕更新|开端|不封号|外部|.* toolbox|替换au|绕过(盒子)vape检测|内部|防封|封号|waibu|晋商|禁商|盒子更新后|小号机|群(号)(:)[0-9]{5,10}|\d{2,4}红利项目|躺赚|咨询(\+)|捡钱(模式)|(个人)创业|带价私聊|出.*号|裙(号)(:)[0-9]{5,10}|君羊(号)(:)[0-9]{5,10}|q(:)[0-9]{5,10}|免费(获取)|.*launcher|3xl?top|.*小卖铺|cpd(d)|hyt|花雨庭|hyp(ixel)|海像素|快乐像素|.*重拳出击.*|回归|暴打|vulcan(反作弊)绕过|aac|watch( )dog|入侵|看门狗|对刀|不服"
Modules = ModuleManager()

class Group:
    def __init__(self, gid):
        self.id = int(gid)

    def get_users(self):
        return getGroupUser(self.id)

    def mute(self, user, mute_time):
        mutePerson(self.id, user.id, mute_time)


class User:
    def __init__(self, uid, nickname):
        self.id = int(uid)
        self.name = nickname

    def add2blacklist(self):
        if self.id not in BLACK_LIST and self.id != 1584784496:
            BLACK_LIST.append(self.id)

    def remove4blacklist(self):
        BLACK_LIST.remove(self.id)

    def isblack(self):
        return self.id in BLACK_LIST

    def isadmin(self):
        return self.id in ADMIN_LIST

    def add2admin(self):
        if self.id not in ADMIN_LIST:
            ADMIN_LIST.append(self.id)

    def remove4admin(self):
        if self.id != 1584784496:
            ADMIN_LIST.remove(self.id)


class Message:
    def __init__(self, JSON=None):
        self.id = 0
        self.text = 0
        self.sender = None
        self.group = None
        if JSON is not None:
            a = json.loads(JSON)
            ad = a
            if ad["post_type"] == "message" and ad["message_type"] == "group":
                self.text = strQ2B(ad["message"])
                self.sender = User(ad["sender"]["user_id"], ad["sender"]["nickname"])
                self.group = Group(ad["group_id"])
                self.id = ad["message_id"]
                self.success = True
            else:
                raise Exception()

    def mute(self, _time):
        self.group.mute(self.sender, _time)

    def recall(self):
        recall(self.id)

    def fastReply(self, message, at=True, reply=True):
        temp1 = [None, None]

        if at:
            temp1[0] = self.sender.id

        if reply:
            temp1[1] = self.id

        sendMessage(message, target_qq=temp1[0], target_group=self.group.id, message_id=temp1[1])


def readConfig():
    global ADMIN_LIST, BLACK_LIST, FEEDBACKS
    config = configparser.ConfigParser()
    config.read("config.ini")
    s = config["DEFAULT"]
    try:
        ADMIN_LIST = [int(i) for i in s["admin"].split(",")]
    except:
        pass
    try:
        BLACK_LIST = [int(i) for i in s["blacklist"].split(",")]
    except:
        pass
    config = configparser.ConfigParser()
    config.read("feedback.ini")
    try:
        FEEDBACKS = config["FEEDBACKS"]
    except:
        pass


def saveConfig():
    global ADMIN_LIST, BLACK_LIST, FEEDBACKS
    config = configparser.ConfigParser()
    config["DEFAULT"] = {
        "admin": ",".join('%s' % _id for _id in ADMIN_LIST),
        "blacklist": ",".join('%s' % _id for _id in BLACK_LIST)
    }
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    config = configparser.ConfigParser()
    config["FEEDBACKS"] = FEEDBACKS
    with open('feedback.ini', 'w') as configfile:
        config.write(configfile)


def quit():
    print("Try to Quit...")
    saveConfig()
    psutil.Process().kill()


def SpammerChecker(msg):
    global ANTISPAMMER
    group = msg.group.id
    user = msg.sender.id
    if group not in ANTISPAMMER:
        ANTISPAMMER[group] = {}
    if user not in ANTISPAMMER[group]:
        ANTISPAMMER[group][user] = [0, 0]
    if time.time() - ANTISPAMMER[group][user][0] <= 15:
        ANTISPAMMER[group][user][1] += 1
    else:
        ANTISPAMMER[group][user][0] = time.time()
        ANTISPAMMER[group][user][1] = 1
    if ANTISPAMMER[group][user][1] >= 8:
        ANTISPAMMER[group][user] = [0, 0]
        return True
    else:
        if msg.text.count("\n") >= 15:
            return True

    return False


def getRuntime():
    nowtime = int(time.time())
    return "{}秒".format(int(nowtime - recordTime))


def text2image(text):
    imageuid = str(random.randint(10000000, 9999999999))
    fontSize = 22
    max_w = 0
    lines = text.split('\n')
    # print(len(lines))
    fontPath = r"a.ttf"
    font = ImageFont.truetype(fontPath, fontSize)
    for i in lines:
        try:
            if max_w <= font.getmask(i).getbbox()[2]:
                max_w = font.getmask(i).getbbox()[2]
        except:
            pass
    im = Image.new("RGB", (max_w + 11, len(lines) * (fontSize + 8)), (255, 255, 255))
    dr = ImageDraw.Draw(im)
    dr.text((1, 1), text, font=font, fill="#000000")
    im.save(imageuid + ".cache.png")
    with open(imageuid + ".cache.png", "rb") as f:
        return base64.b64encode(f.read()).decode()


def strQ2B(ustring):
    rstring = ""
    for uchar in ustring:
        inside_code = ord(uchar)
        if inside_code == 12288:
            inside_code = 32
        elif 65281 <= inside_code <= 65374:
            inside_code -= 65248

        rstring += chr(inside_code)
    return rstring


def acg_img():
    try:
        a = "https://img.xjh.me/random_img.php?return=json"
        a1 = requests.get(url=a).json()
        return base64.b64encode(requests.get(url='https:' + a1["img"]).content).decode()
    except Exception as e:
        return text2image("获取图片失败\n" + traceback.format_exc())


def on_message2(ws, message):
    global HYPBAN_COOKIE, isChatBypassOpened, CACHE_MESSAGE, timePreMessage, MESSAGE_PRE_MINUTE, ALL_MESSAGE, ALL_AD, FEEDBACKS, cmd
    msg = Message(message)

    try:
        # 处理消息内容
        if msg.text == "":
            return
        if time.time() - MESSAGE_PRE_MINUTE[0] >= 60:
            MESSAGE_PRE_MINUTE = [time.time(), 1]
        else:
            MESSAGE_PRE_MINUTE[1] += 1
        ALL_MESSAGE += 1

        print("[{0}] {1}({2}) {3}".format(msg.group.id, msg.sender.name, msg.sender.id, msg.text))

        reScan = re.findall(
            ANTI_AD,
            msg.text.replace(" ", "").replace(".", "").replace("\n", "").lower())
        if len(msg.text) > 35 and len(reScan) >= 2:
            if msg.sender.isadmin():
                sendMessage("{}发送的一条消息触发了正则 并且此人在超管名单内\n内容:\n{}".format(msg.sender.id, msg.text),
                            target_group=308089090)
                return
            msg.mute(3600)
            msg.recall()
            ALL_AD += 1
            return

        sc_id_ad = re.search(ANTI_AD, msg.sender.name.replace(" ", "").replace(".", "").replace("\n", "").lower())
        if sc_id_ad is not None and not msg.sender.isadmin():
            msg.mute(600)
            msg.recall()
            time.sleep(random.randint(500, 2000) / 1000)
            msg.fastReply("您的名称中似乎存在广告", reply=False)
            ALL_AD += 1
            return

        if len(msg.text) > 1500:
            msg.mute(600)
            msg.recall()
            msg.fastReply("消息太长了哟", reply=False)
            return

        multiMsg = re.search(r'\[CQ:forward,id=(.*)]', msg.text)
        if multiMsg is not None:
            a = requests.get(url="http://" + HTTPURL + "/get_forward_msg?message_id=" + str(multiMsg.group(1))).json()[
                "data"]["messages"]
            multiMsg_raw = ""
            for i in a:
                multiMsg_raw += i["content"]
            reScan = re.search(
                ANTI_AD,
                multiMsg_raw.replace(" ", "").replace(".", "").replace("\n", "").lower())
            if reScan is not None:
                msg.fastReply("您发送的合并转发内容貌似有广告!", reply=False)
                msg.mute(3600)
                msg.recall()
                ALL_AD += 1
                return

        try:
            if SpammerChecker(msg):
                msg.mute(60)
                msg.recall()
                msg.fastReply("不要刷屏哟~~", reply=False)
        except:
            pass

        if msg.sender.id in BLACK_LIST:
            msg.mute(60)
            msg.recall()
            return

        if msg.text.count("[CQ:image") >= 3:
            if msg.sender.isadmin() is False:
                msg.mute(60)
                msg.recall()
                msg.fastReply("太...太多图片了..", reply=False)
                return
        
        command_list = msg.text.split(" ")
        
        if (msg.group.id, msg.sender.id) in REPEATER:
            msg.fastReply(msg.text, reply=False, at=False)

        if msg.text == "!quit" and msg.sender.isadmin():
            msg.fastReply("正在尝试这么做...")
            quit()
        
        if msg.text == "!reload" and msg.sender.isadmin():
            Modules.load()
            msg.fastReply("Reloaded!")

        if msg.text in ["!test", "凌状态"]:
            msg.fastReply(
                "Hello! 已处理 {} 条消息\n已经运行了 {}\n平均每条消息耗时 {} 秒\n拦截了 {} 条广告 占全部处理消息的 {}%".format(
                    ALL_MESSAGE,
                    getRuntime(),
                    timePreMessage,
                    ALL_AD,
                    (ALL_AD / ALL_MESSAGE) * 100
                )
            )

        if command_list[0] in ["!help", "菜单"]:
            msg.fastReply("请访问: https://lingbot.guimc.ltd/\nLingbot官方群：308089090")

        if msg.text == "一语":
            msg.fastReply(requests.get("http://api.muxiuge.cn/API/society.php").json()["text"])

        if msg.text == "!testzb":
            goodmor(target=msg.group.id)

        if msg.text.find("[CQ:json,data=") != -1:
            msg.text = msg.text.replace("\\", "")
            if msg.text.find('https://b23.tv/') != -1:
                str1 = requests.get(url="https://api.bilibili.com/x/web-interface/view?bvid={}".format(
                    re.findall(r'<link data-vue-meta="true" rel="canonical" href="https://www.bilibili.com/video/.*/">',
                               requests.get(json.loads(
                                   re.search(r"\[CQ:json,data=(.*)]", msg.text).group(1).replace("&amp;", "&"))[
                                                "meta"]["news"]["jumpUrl"]).text)[0].replace(
                        r'<link data-vue-meta="true" rel="canonical" href="https://www.bilibili.com/video/', "")[:-3])).json()

                if str1["code"] != 0:
                    print("查询失败")
                    return
                str1 = str1["data"]
                response = requests.get(str1["pic"])
                im_vl = Image.open(BytesIO(response.content))
                im_v = im_vl.resize((430, 270), Image.ANTIALIAS)
                imageuid = str(random.randint(10000000, 9999999999))
                fontSize = 22
                max_w = 0
                s = ""
                if str1["copyright"] == 1:
                    s = "自制"
                elif str1["copyright"] == 2:
                    s = "转载"
                else:
                    s = f"未曾设想的投稿类型: {str1['copyright']}  (不是转载也不是自制?)"
                text = f"""标题: {str1["title"]}
UP主: {str1["owner"]["name"]} ({str1["owner"]["mid"]})
投稿分区: {str1["tname"]} ({str1["tid"]})
投稿类型: {s}
视频链接: https://www.bilibili.com/video/{str1["bvid"]}/
播放量: {str1["stat"]["view"]}
简介:
{str1["desc"]}"""  # :(
                lines = text.split('\n')
                # print(len(lines))
                fontPath = r"a.ttf"
                font = ImageFont.truetype(fontPath, fontSize)
                for i in lines:
                    try:
                        if max_w <= font.getmask(i).getbbox()[2]:
                            max_w = font.getmask(i).getbbox()[2]
                    except:
                        pass
                im = Image.new("RGB", (max_w + 11, (len(lines) * (fontSize + 8)) + 280), (255, 255, 255))
                im.paste(im_v, (0, 0))
                dr = ImageDraw.Draw(im)
                dr.text((1, 280), text, font=font, fill="#000000")
                im.save(imageuid + "_cache.png")
                with open(imageuid + "_cache.png", "rb") as f:
                    msg.fastReply("[CQ:image,file=base64://" + base64.b64encode(f.read()).decode() + "]")

        # if msg.text == "一英":
        #     msg.fastReply(requests.get("http://open.iciba.com/dsapi/").json()["content"] + "\n" +
        #                   requests.get("http://open.iciba.com/dsapi/").json()["note"])

        # if msg.text == "二次元":
        #     msg.fastReply("[CQ:image,file=base64://" + acg_img() + "]")

        if msg.text == "必应壁纸":
            msg.fastReply("[CQ:image,file=base64://" + base64.b64encode(
                requests.get("http://www.xgstudio.xyz/api/bing.php").content).decode() + "]")

        if msg.text == "一话":
            req1 = requests.get("http://open.iciba.com/dsapi/").json()
            msg.fastReply(
                requests.get("http://api.muxiuge.cn/API/society.php").json()["text"])
            msg.fastReply(req1["content"] + "\n" + req1["note"])
        
        if msg.text == "!hyp players":
            _all_modes = hypixel.getJSON("counts")
            _all_player = _all_modes["playerCount"]
            _all_modes = _all_modes["games"]
            _all_players = []
            for i in _all_modes:
                _all_players.append(_all_modes[i]["players"])
            
            temp_msg = ""
            temp_list = []
            for i in _all_modes.items():
                temp_list.append(i)
            for i in range(len(_all_modes)):
                try:
                    temp_msg += "{}: {} ({}%)\n".format(temp_list[i][0], _all_players[i], round((_all_players[i]/_all_player)*100, 2))
                except Exception as e:
                    print(e)
            print(temp_msg)
            msg.fastReply("[CQ:image,file=base64://{}]".format(text2image(temp_msg)))
            return
        
        if command_list[0] == "!repeater":
            if msg.sender.isadmin():
                if command_list[1] == "add":
                    if (msg.group.id, int(command_list[2])) in REPEATER:
                        msg.fastReply("复读机名单内已经有这个人了")
                        return
                    REPEATER.append((msg.group.id, int(command_list[2])))
                    msg.fastReply("操作成功")
                elif command_list[1] == "remove":
                    if (msg.group.id, int(command_list[2])) not in REPEATER:
                        msg.fastReply("复读机名单内没有这个人")
                        return
                    REPEATER.remove((msg.group.id, int(command_list[2])))
                    msg.fastReply("操作成功")

        if command_list[0] == "!tcping":
            if len(command_list) == 1:
                msg.fastReply("语法错误 使用方法为: !tcping IP[:端口(默认为80)]\n如: !tcping api.github.com:80")
            else:
                msg.fastReply("正在进行TCPing")
                _host = ""
                _port = "80"
                if command_list[1].find(":") != -1:
                    _host, _port = command_list[1].split(":")
                else:
                    _host = command_list[1]
                
                _ping = tcping.Ping(_host, int(_port), 1.0)
                _ping.ping(5)
                msg.fastReply("[CQ:image,file=base64://{}]".format(text2image(_ping.result.raw.replace(", ", "\n"))))


        if command_list[0] == "!admin":
            if command_list[1] == "list":
                msg.fastReply(", ".join('%s' % id for id in ADMIN_LIST))
            elif not msg.sender.isadmin():
                msg.fastReply("你的权限不足!")
                return
            if command_list[1] == "add":
                if int(command_list[2]) in ADMIN_LIST:
                    msg.fastReply("超管内已经有这个人了")
                    return
                ADMIN_LIST.append(int(command_list[2]))
                msg.fastReply("操作成功")
            elif command_list[1] == "remove":
                if int(command_list[2]) not in ADMIN_LIST:
                    msg.fastReply("超管内没有这个人")
                    return
                elif int(command_list[2]) == 1584784496:
                    msg.fastReply("不可以这么干哟~~")
                    sendMessage("{}尝试把您(Owner)从超管列表删除".format(msg.sender.id), target_group=868218262)
                    return
                ADMIN_LIST.remove(int(command_list[2]))
                msg.fastReply("操作成功")

        if command_list[0] == "!blacklist":
            if command_list[1] == "list":
                msg.fastReply(", ".join('%s' % id for id in BLACK_LIST))
            elif not msg.sender.isadmin():
                msg.fastReply("你的权限不足!")
                return
            if command_list[1] == "add":
                if int(command_list[2]) in BLACK_LIST:
                    msg.fastReply("黑名单内已经有这个人了")
                    return
                elif int(command_list[2]) == 1584784496:
                    msg.fastReply("不可以这么干哦~~")
                    sendMessage("{}尝试把您(Owner)添加进黑名单".format(msg.sender.id), target_group=868218262)
                    return
                BLACK_LIST.append(int(command_list[2]))
                msg.fastReply("操作成功")
            elif command_list[1] == "remove":
                if int(command_list[2]) not in BLACK_LIST:
                    msg.fastReply("黑名单内没有这个人")
                    return
                BLACK_LIST.remove(int(command_list[2]))
                msg.fastReply("操作成功")

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
            msg.fastReply(aaa)

        if command_list[0] == "!hypban":
            msg.fastReply("本功能已经停止使用了")
            return
            # if len(command_list)<=2:
            #     msg.fastReply("正确格式:#hypban <USERNAME> <BANID>")
            # else:
            #     if msg.sender.id not in BANCHECK_UID or msg.sender.id in ADMIN_LIST:
            #         BANCHECK_UID[msg.sender.id] = time.time()
            #     elif time.time() - BANCHECK_UID[msg.sender.id] <= 60:
            #         msg.fastReply("进入冷却时间 可在{}秒后使用".format(round(60.0 - (time.time() - BANCHECK_UID[msg.sender.id]), 2)))
            #         return
            #     msg.fastReply("请稍等 正在向远程服务器发送请求")
            #     userName = command_list[1]
            #     BanID = command_list[2].replace("#", "")
            #     while True:
            #         print("Username:{} BanID:{}".format(userName, BanID))
            #         a = requests.get("http://127.0.0.1/hypban.php?name={0}&banid={1}&type=api".format(userName, BanID), headers={'Host': 'api.getfdp.today'}).text
            #         if a.find("too many request") == -1:
            #             break
            #         time.sleep(3)
            #     print(a)
            #     if a.find("ERR|") != -1:
            #         msg.fastReply(a)
            #     else:
            #         BANCHECK_UID[msg.sender.id] = time.time()
            #         msg.fastReply( "[CQ:image,file=base64://"+text2image(a)+"]")

        if command_list[0] == "!send":
            if msg.sender.isadmin():
                msg1 = " ".join(command_list[2:])
                all_req = re.match(REQ_TEXT, msg1)
                print(all_req)
                if all_req is not None:
                    msg1 = msg1.replace(all_req.group(0), urlget(all_req.group(0).replace("get±", "").replace("±", "")))
                if command_list[1] == "all":
                    s = getGroups()
                    msg.fastReply("正在群发... 目标:{}个群".format(len(s)))
                    _prefix = "(由 {}({}) 发起的群发消息)".format(msg.sender.name, msg.sender.id)
                    for i in s:
                        if i not in IGNORE_GROUP:
                            sendMessage(_prefix + msg1, target_group=i)
                            time.sleep(random.randint(1500, 1900) / 1000)
                    msg.fastReply("群发完成")
                else:
                    sendMessage(msg1, target_group=command_list[1])
            else:
                msg.fastReply("你的权限不足!")

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
                    mutePerson(command_list[1], command_list[2], command_list[3] * 60)
                    msg.fastReply("已尝试在群 {} 禁言 {} {}分钟".format(command_list[1], command_list[2], command_list[3]))
            else:
                msg.fastReply("你的权限不足!")

        if command_list[0] == "!namelocker":
            msg.fastReply("恭喜你找到了一个彩蛋!")
            # 鬼!
            return

        if command_list[0] == "!search":
            if not msg.sender.isadmin():
                msg.fastReply("你的权限不足!")
                return
            msg.fastReply("正在从机器人所有加入的群搜索此人")
            a = search_user(int(command_list[1]))
            msg.fastReply("搜索完成:\n{}".format(a))

        if command_list[0] == "!fdpinfo":
            if command_list[1] == "online":
                url = "https://bstats.org/api/v1/plugins/11076/charts/minecraftVersion/data"
                a = requests.get(url=url).json()
                onlinePlayer = 0
                for i in a:
                    onlinePlayer += i["y"]
                msg.fastReply("[CQ:image,file=base64://" + text2image("OnlinePlayers: {}".format(onlinePlayer)) + "]")
            elif command_list[1] == "versions":
                url = "https://bstats.org/api/v1/plugins/11076/charts/pluginVersion/data"
                a = requests.get(url=url).json()
                onlineVersion = []
                for i in a:
                    onlineVersion.append("{}: {}".format(i["name"], i["y"]))
                msg.fastReply("[CQ:image,file=base64://" + text2image(
                    "OnlineVersionsInfo:\n{}".format("\n".join(onlineVersion))) + "]")
            elif command_list[1] == "systems":
                url = "https://bstats.org/api/v1/plugins/11076/charts/os/data"
                a = requests.get(url=url).json()
                onlineSystem = []
                for i in a["seriesData"]:
                    onlineSystem.append("{}: {}".format(i["name"], i["y"]))
                msg.fastReply(
                    "[CQ:image,file=base64://" + text2image("OnlineSystms:\n{}".format("\n".join(onlineSystem))) + "]")
            elif command_list[1] == "countries":
                url = "https://bstats.org/api/v1/plugins/11076/charts/location/data"
                a = requests.get(url=url).json()
                onlineCountry = []
                for i in a:
                    onlineCountry.append("{}: {}".format(
                        i["name"].replace("Hong Kong", "Hong Kong, China").replace("Taiwan", "Taiwan, China"),
                        i["y"]))
                msg.fastReply("[CQ:image,file=base64://" + text2image(
                    "OnlineCountrys:\n{}".format("\n".join(onlineCountry))) + "]")
            elif command_list[1] == "beta":
                msg.fastReply("Please wait...")
                url = "https://api.github.com/repos/UnlegitMC/FDPClient/actions/runs"
                a = requests.get(url=url).json()
                objectIDs = []
                for i in a["workflow_runs"]:
                    if i["name"] == "build":
                        objectIDs.append(i["id"])
                actionInfo = requests.get(
                    url="https://api.github.com/repos/UnlegitMC/FDPClient/actions/runs/{}".format(objectIDs[0])).json()
                upd_time = actionInfo["head_commit"]["timestamp"]
                updMsg = actionInfo["head_commit"]["message"]
                updAuthor = "{} ({})".format(actionInfo["head_commit"]["author"]["name"],
                                             actionInfo["head_commit"]["author"]["email"])
                msg.fastReply("Update Time:{}\n"
                              "Update Message:{}\n"
                              "Author:{}\n"
                              "Download URL:https://nightly.link/UnlegitMC/FDPClient/actions/runs/{}/FDPClient.zip\n".format(upd_time, updMsg, updAuthor, objectIDs[0]))
            elif command_list[1] == "release":
                url = "https://api.github.com/repos/UnlegitMC/FDPClient/releases/latest"
                a = requests.get(url=url).json()
                files = []
                for i in a["assets"]:
                    files.append(
                        "{}: {}".format(i["name"], i["browser_download_url"].replace("github.com", "hub.fastgit.org")))
                msg.fastReply("Version: {}\n".format(a["name"]) + "\n".join(files))
        if command_list[0] == "!hyp":
            if len(command_list) == 1:
                msg.fastReply("格式貌似有点问题?\n访问 https://lingbot.guimc.ltd/#/Commands 找一找你想要的功能罢")
                return

            # 获取玩家信息
            try:
                player1 = hypixel.Player(command_list[1])
            except hypixel.PlayerNotFoundException:
                msg.fastReply("貌似没有这个玩家?\n访问 https://lingbot.guimc.ltd/#/Commands 找一找你想要的功能罢")
                return
            pI = player1.getPlayerInfo()
            print(pI)
            if "lastLogin" not in pI:
                pI["lastLogin"] = 0
            if 'karma' not in pI:
                pI["karma"] = "0"
            playerSkin = requests.get("https://crafatar.com/renders/body/" + pI["uuid"])

            lastLogout = 0
            if "lastLogout" in player1.JSON:
                lastLogout = player1.JSON["lastLogout"]
            
            onlineMode = None
            try:
                _onlineStatus = hypixel.getJSON("status", uuid=pI["uuid"])["session"]
                _isOnline = _onlineStatus["online"]
                if _isOnline:
                    onlineMode = "Online: {} - {} ({})".format(_onlineStatus["gameType"], _onlineStatus["mode"], _onlineStatus["map"])
                else:
                    onlineMode = "Offline"
            except:
                pass

            pmsg = """注: 当前为测试版本 不代表最终体验
---查询结果---
玩家名称: [{rank}]{name}
等级: {level}
Karma(人品值): {karma}
上次登陆: {last_login}
上次登出: {lastLogout}[{onlineMode}]
首次登陆: {first_login}""".format(
                rank = player1.getRank()["rank"].replace(" PLUS", "+"),
                name = pI["displayName"],
                level = player1.getLevel(),
                karma = pI["karma"],
                last_login = datetime.datetime.utcfromtimestamp(pI["lastLogin"] / 1000).strftime("%Y-%m-%d %H:%M:%S"),
                first_login = datetime.datetime.utcfromtimestamp(pI["firstLogin"] / 1000).strftime("%Y-%m-%d %H:%M:%S"),
                onlineMode = onlineMode,
                lastLogout = datetime.datetime.utcfromtimestamp(lastLogout / 1000).strftime("%Y-%m-%d %H:%M:%S"))

            if playerSkin.status_code == 200:
                pmsg = "[CQ:image,file=base64://" + base64.b64encode(playerSkin.content).decode() + "]\n" + pmsg

            try:
                sbplayer = hypixel.getJSON('skyblock/profiles', uuid=pI['uuid'])
                profile_id = sbplayer["profiles"][0]["profile_id"]
                sbprofile = sbplayer["profiles"][0]["members"][profile_id]
                finished_quests = 0
                for i in sbprofile["quests"]:
                    if sbprofile["quests"][i]["status"] == "COMPLETE":
                        finished_quests += 1
                pmsg += """\n---SkyBlock---
Profile ID: {profile_id}
上次保存: {last_save}
第一次进入: {first_join}
Coins: {coin_purse}
已经完成的任务: {finished_quests}
进入过的区域: {visited_zones}个
死亡次数: {death_count}""".format(profile_id=profile_id,
                              last_save=datetime.datetime.utcfromtimestamp(sbprofile["last_save"] / 1000).strftime(
                                  "%Y-%m-%d %H:%M:%S"),
                              first_join=datetime.datetime.utcfromtimestamp(sbprofile["first_join"] / 1000).strftime(
                                  "%Y-%m-%d %H:%M:%S"),
                              coin_purse=sbprofile["coin_purse"],
                              finished_quests=finished_quests,
                              visited_zones=len(sbprofile["visited_zones"]),
                              death_count=sbprofile["death_count"])
            except:
                print(traceback.format_exc())
            msg.fastReply(pmsg)

        if command_list[0] in Modules.func_dist:
            Modules.func_dist[command_list[0]](msg, command_list)
    except Exception as e:
        a = traceback.format_exc()
        msg.fastReply("很抱歉，我们在执行你的指令时出现了一个问题 =_=\n各指令用法请查看 https://lingbot.guimc.ltd/\n[CQ:image,file=base64://{}]".format(text2image(a)))
        print(a)


def mutePerson(group, qq_number, mute_time):
    if mute_time > (43199 * 60):
        mute_time = 43199 * 60
    data1 = {
        "group_id": int(group),
        "user_id": int(qq_number),
        "duration": int(mute_time)
    }
    requests.post(url="http://" + HTTPURL + "/set_group_ban", data=data1)


def unmutePerson(group, qq_number):
    mutePerson(group, qq_number, 0)


def recall(msg_id):
    data1 = {
        "message_id": int(msg_id)
    }
    requests.post(url="http://" + HTTPURL + "/delete_msg", data=data1)


def sendMessage(message, target_qq=None, target_group=None, message_id=None):
    if target_qq is None and target_group is None:
        raise Exception()

    if target_group is not None:
        # 消息前缀 通常用于 At 回复消息
        prefix = ""

        if target_qq is not None:
            prefix += "[CQ:at,qq={}]".format(target_qq)

        if message_id is not None:
            prefix += "[CQ:reply,id={}]".format(message_id)

        # 构建数据
        data1 = {
            "group_id": int(target_group),
            "message": prefix + message
        }

        # 发送消息
        s = requests.post(url="http://" + HTTPURL + "/send_group_msg", data=data1)
        if not s.ok:
            # 如果请求失败
            s.raise_for_status()
    else:
        print("WARN: 目前暂时不支持发送私聊消息")


def urlget(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 4 Build/JOP40D) AppleWebKit/535.19 (KHTML, '
                      'like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19'}
    temp = requests.get(url, headers=headers)
    return temp.text


def sendTempMsg(target1, target2, text):
    # 会风控
    print(text)


def getGroupUser(groupID: int):
    users = []
    a = requests.get(url="http://" + HTTPURL + "/get_group_member_list?group_id={}".format(groupID))
    if a.status_code != 200:
        raise ConnectionError()
    else:
        for i in a.json()["data"]:
            users.append(i["user_id"])
        return users


def getGroups():
    groups = []
    a = requests.get(url="http://" + HTTPURL + "/get_group_list")
    if a.status_code != 200:
        raise ConnectionError()
    else:
        print(a.json()["data"])
        for i in a.json()["data"]:
            groups.append(i["group_id"])
        return groups


def permCheck(groupID, target):
    return True


def search_user(uid):
    groups = []
    for i in getGroups():
        if uid in getGroupUser(i):
            groups.append(i)
        time.sleep(random.randint(35, 65) / 100)
    return groups


def temps_message(ws, message):
    global timePreMessage
    a = time.time()
    try:
        on_message2(ws, message)
    except:
        pass
    b = time.time()
    sflTime = b - a
    if timePreMessage == 0:
        timePreMessage = sflTime
    else:
        timePreMessage = (timePreMessage + sflTime) / 2


# 定义一个用来接收监听数据的方法
def on_message(ws, message):
    threading.Thread(target=temps_message, args=(ws, message)).start()


# 定义一个用来处理错误的方法
def on_error(ws, error):
    print("-----连接出现异常,异常信息如下-----")
    print(error)


# 定义一个用来处理关闭连接的方法
def on_close(ws, a, b):
    print("-------连接已关闭------")


def goodmor(target=None):
    msg1 = "早上好呀~ [CQ:image,file=base64://{}]".format(
        text2image(requests.get(url="https://www.ipip5.com/today/api.php?type=txt", verify=False).text))
    s = getGroups()
    if target:
        sendMessage(msg1, target_group=target)
    else:
        for i in s:
            sendMessage(msg1, target_group=i)
            time.sleep(random.randint(1500, 2000) / 1000)


def goodnig():
    msg1 = "很晚了!该睡了!"
    s = getGroups()
    for i in s:
        sendMessage(msg1, target_group=i)
        time.sleep(random.randint(700, 1100) / 1000)


def main():
    try:
        print("Starting... (0/5)")
        readConfig()
        print("Starting... (1/5)")
        ws = websocket.WebSocketApp("ws://" + WSURL + "/all?verifyKey=uThZyFeQwJbD&qq=3026726134",
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close,
                                    )
        t3 = threading.Thread(target=ws.run_forever)
        t3.daemon = True
        print("Starting... (2/5)")
        sched = BlockingScheduler()
        sched.add_job(goodmor, 'cron', hour=7)
        sched.add_job(goodnig, 'cron', hour=22, minute=30)
        t1 = threading.Thread(target=sched.start)
        t1.deamon = True
        print("Starting... (3/5)")
        t1.start()
        print("Starting... (4/5)")
        t3.start()
        print("Starting... (5/5)")
        Modules.load()
        print("Bot Ready!")
        while True:
            time.sleep(3600)
        # quit()  Reason: Code is unreachable
    except KeyboardInterrupt:
        quit()
    except Exception:
        print("遇到无法恢复的错误 即将退出")
        print(traceback.format_exc())
        quit()


main()
