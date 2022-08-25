# -*- coding: UTF-8 -*-
import base64
import configparser
import datetime
import json
import logging
import os
import random
import re
import threading
import time
import traceback
import datetime
from io import BytesIO
from xmlrpc.client import Boolean
# test
import hypixel
import psutil
import requests
import websocket
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from apscheduler.schedulers.blocking import BlockingScheduler
from mcstatus import MinecraftServer
from simhash import Simhash
import math
import chinese_sensitive_vocabulary.word_filter
from events.Events import Event, GroupMessageEvent
from module.ModulesManager import ModuleManager
from utils import five_k_utils, tcping

hypixel.setKeys(["14741cb9-194f-4c5b-adb2-9490b1240f14", "2ca19e21-eb6d-4aaa-9ceb-91f4718c8bd9"])
hypixel.setCacheTime(10.0)
logging.basicConfig(level=logging.DEBUG, format="[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%H:%M:%S %p")


def get_achievement_image(block, title, string1, string2=None):
    title = title.replace(" ", "..")
    string1 = string1.replace(" ", "..")
    if string2 is not None:
        string2 = string2.replace(" ", "..")
    return f'https://minecraft-api.com/api/achivements/{block}/{title}/{string1}/{string2 if string2 is not None else ""}'


ACCOMPLISHMENT = {"qq": {}, "ACCOMPLISHMENT": {
    "i_m_stupid": get_achievement_image("sand", "STUPID", "I am stupid"),
    "a_night_person": get_achievement_image("totem_of_undying", "A NIGHT PERSON",
                                            "People are in China, the time difference is in foreign countries",
                                            "Remember to go to bed early")
}}
# https://minecraft-api.com/achivements/blocks/
SERVER_ADDR = "127.0.0.1"
ADMIN_LIST = []
HYPBAN_COOKIE = None
SEND_AD_LIST = {}
BLACK_LIST = []
INTRODUCE = {"qq": {}, "waiting": []}
CACHE_MESSAGE = []
BANCHECK_UID = {}
WSURL = SERVER_ADDR + ":10540"
HTTPURL = SERVER_ADDR + ":10500"
MC_MOTD_COLORFUL = re.compile(r"§.")
ALL_MESSAGE = 0
MESSAGE_PRE_MINUTE = [0, 0]
ALL_AD = 0
BILI_BV_RE = re.compile(r"BV([a-zA-Z\d]{10})")
timePreMessage = 0
recordTime = int(time.time())
isChatBypassOpened = False
ANTISPAMMER = {}
IGNORE_GROUP = [1079822858]
FOLLOW_MUTE = {}
MESSAGE_COUNTER = {}
FEEDBACKS = {}
REPEATER = []
AUTISM = []
SPAM2_MSG = {}
SPAM2_VL = {}
SPAM2_MESSAGE_LIST = {}
SCREENSHOT_CD = 0
EMAIL_DELAY = {}
VERIFIED = {}
VERIFYING = {}
VERIFY_TIPS = {}
last_info = ""
msg_scanner = chinese_sensitive_vocabulary.word_filter.SensitiveWordModel(
    chinese_sensitive_vocabulary.word_filter.word_url)
moduleManager: ModuleManager = ModuleManager()

# URL_LIST = r'http(s)://[(.*).net|.com|.xyz|.me|.top]'
ANTI_AD = r"送福利|定制水影|加群.*[0-9]{5,10}|.*内部|\n元|破甲|天花板|工具箱|绕更新|开端|不封号|外部|.* toolbox|替换au|绕过(盒子)vape检测|内部|防封|封号|waibu|外部|.*公益|晋商|禁商|盒子更新后|小号机|群.*[0-9]{5,10}|\d{2,4}红利项目|躺赚|咨询(\+)|捡钱(模式)|(个人)创业|带价私聊|出.*号|裙.*[0-9]{5,10}|君羊.*[0-9]{5,10}|q(\:)[0-9]{5,10}|免费(获取)|.*launcher|3xl?top|.*小卖铺|cpd(d)|暴打|对刀|不服|稳定奔放|qq[0-9]{5,10}|定制.*|小卖铺|老婆不在家(刺激)|代购.*|vape"

spam2_vl_reset_cool_down = time.time()


class Group:
    def __init__(self, gid):
        self.id = int(gid)

    def get_users(self):
        return getGroupUser(self.id)

    def mute(self, user, mute_time):
        mutePerson(self.id, user.id, mute_time)

    def isverify(self):
        if str(self.id) in VERIFIED:
            return True
        return False

    def verify_info(self):
        if str(self.id) in VERIFIED:
            return f"已验证 绑定邮箱:{''.join(VERIFIED[str(self.id)][0:3])}{len(VERIFIED[str(self.id)][3:-3]) * '*'}{''.join(VERIFIED[str(self.id)][-3:])}"
        elif str(self.id) in VERIFYING:
            return f"正在验证..."
        else:
            return f"未验证! 请使用 !mail 指令查看如何激活"


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
    def __init__(self, json2msg=None):
        self.id = 0
        self.text = 0
        self.sender = None
        self.group = None
        self.JSON = json2msg
        if json2msg is not None:
            a = json.loads(json2msg)
            ad = a
            if ad["post_type"] == "message" and ad["message_type"] == "group":
                self.text = strQ2B(ad["message"])
                self.sender = User(ad["sender"]["user_id"], ad["sender"]["nickname"])
                self.group = Group(ad["group_id"])
                self.id = ad["message_id"]
                self.text_nocq = re.sub(r"\[CQ:.*]", '', self.text)
                self.success = True
            else:
                raise Exception()

    def mute(self, _time):
        self.group.mute(self.sender, _time)
        return self

    def recall(self):
        recall(self.id)
        return self

    def fast_reply(self, message, at=True, reply=True):
        temp1 = [None, None]

        if at:
            temp1[0] = self.sender.id

        if reply:
            temp1[1] = self.id

        sendMessage(message, target_qq=temp1[0], target_group=self.group.id, message_id=temp1[1])
        return self


def crop_max_square(pil_img):
    return crop_center(pil_img, min(pil_img.size), min(pil_img.size))


def crop_center(pil_img, crop_width, crop_height):
    img_width, img_height = pil_img.size
    return pil_img.crop(((img_width - crop_width) // 2,
                         (img_height - crop_height) // 2,
                         (img_width + crop_width) // 2,
                         (img_height + crop_height) // 2))


def mask_circle_transparent(pil_img, blur_radius, offset=0):
    offset += blur_radius * 2
    mask = Image.new("L", pil_img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((offset, offset, pil_img.size[0] - offset, pil_img.size[1] - offset), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(blur_radius))

    result = pil_img.copy()
    result.putalpha(mask)
    return result, mask


def read_config():
    global ADMIN_LIST, BLACK_LIST, FEEDBACKS, VERIFIED, FOLLOW_MUTE, MESSAGE_COUNTER
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
    try:
        with open('json_list.txt', mode="r", encoding="UTF-8") as jsonfile:
            json_list = json.loads(jsonfile.read())
            INTRODUCE["qq"] = json_list["INTRODUCE"]
            ACCOMPLISHMENT["qq"] = json_list["ACCOMPLISHMENT"]
    except:
        pass
    config = configparser.ConfigParser()
    config.read("feedback.ini")
    try:
        FEEDBACKS = config["FEEDBACKS"]
    except:
        pass

    config.read("verify.ini")
    try:
        VERIFIED = config["VERIFIED"]
    except:
        pass

    try:
        with open("fillow_mute.json", 'r') as f:
            FOLLOW_MUTE = json.loads(f.read())
    except:
        pass

    try:
        with open("message_counter.json") as f:
            MESSAGE_COUNTER = json.loads(f.read())
    except:
        pass
    sendMessage("restart successful", target_group=1019068934)


def save_config():
    global ADMIN_LIST, BLACK_LIST, FEEDBACKS, FOLLOW_MUTE
    config = configparser.ConfigParser()
    config["DEFAULT"] = {
        "admin": ",".join('%s' % _id for _id in ADMIN_LIST),
        "blacklist": ",".join('%s' % _id for _id in BLACK_LIST)
    }
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    json_list = {
        "INTRODUCE": INTRODUCE['qq'],
        "ACCOMPLISHMENT": ACCOMPLISHMENT['qq']
    }
    with open('json_list.txt', 'w', encoding='UTF-8') as jsonfile:
        jsonfile.write(json.dumps(json_list))
    config = configparser.ConfigParser()
    config["FEEDBACKS"] = FEEDBACKS
    with open('feedback.ini', 'w') as configfile:
        config.write(configfile)
    config = configparser.ConfigParser()
    config["VERIFIED"] = VERIFIED
    with open("verify.ini", 'w') as configfile:
        config.write(configfile)
    try:
        with open("fillow_mute.json", 'w') as f:
            f.write(json.dumps(FOLLOW_MUTE))
    except:
        pass

    try:
        with open("message_counter.json", "w") as f:
            f.write(json.dumps(MESSAGE_COUNTER))
    except:
        pass


def stop():
    logging.info("Restarting...")
    save_config()
    psutil.Process().kill()


def spammer_checker(msg):
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
    if ANTISPAMMER[group][user][1] >= 12:
        ANTISPAMMER[group][user] = [0, 0]
        return True
    elif ANTISPAMMER[group][user][1] >= 7 and SPAM2_VL[msg.sender.id] >= 160:
        ANTISPAMMER[group][user] = [0, 0]
        SPAM2_VL[msg.sender.id] -= 7
        return True

    return False


def simhash_similarity(text1: str, text2: str) -> float:
    """
    :param text1: 文本1
    :param text2: 文本2
    :return: 返回两篇文章的相似度
    """
    aa_simhash = Simhash(text1)
    bb_simhash = Simhash(text2)
    max_hashbit = max(len(bin(aa_simhash.value)), (len(bin(bb_simhash.value))))
    # 汉明距离
    distince = aa_simhash.distance(bb_simhash)
    similar = 1 - distince / max_hashbit
    return similar


def get_lapsetime(atime, btime=0) -> str:
    """
    :param atime: 时间1
    :param btime: 时间2
    :return: 返回时间差
    """
    timex = round(atime - btime)
    if timex < 60:
        return f"{timex}秒"
    elif timex < 3600:
        mtime = int((timex - (timex % 60)) / 60)
        return f"{mtime}分{(timex % 60)}秒"
    elif timex < 86400:
        htime = int((timex - (timex % 3600)) / 3600)
        mtime = int((timex - (timex % 60) - (htime * 3600)) / 60)
        return f"{htime}时{mtime}分{(timex % 60)}秒"
    else:
        dtime = int((timex - (timex % 86400)) / 86400)
        htime = int((timex - (timex % 3600) - (timex - (timex % 86400))) / 3600)
        mtime = int((timex - (timex % 60) - (htime * 3600) - (dtime * 86400)) / 60)
        return f"{dtime}天{htime}时{mtime}分{(timex % 60)}秒"


def get_runtime():
    nowtime = int(time.time())
    return get_lapsetime(nowtime, recordTime)


def text2image(text):
    imageuid = str(random.randint(10000000, 9999999999))
    font_size = 22
    max_w = 0
    lines = text.split('\n')
    # print(len(lines))
    font_path = r"a.ttf"
    font = ImageFont.truetype(font_path, font_size)
    for i in lines:
        try:
            if max_w <= font.getmask(i).getbbox()[2]:
                max_w = font.getmask(i).getbbox()[2]
        except:
            pass
    im = Image.new("RGB", (max_w + 11, len(lines) * (font_size + 8)), (255, 255, 255))
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
    global moduleManager, HYPBAN_COOKIE, isChatBypassOpened, \
        CACHE_MESSAGE, timePreMessage, \
        MESSAGE_PRE_MINUTE, ALL_MESSAGE, \
        ALL_AD, FEEDBACKS, \
        spam2_vl_reset_cool_down, SCREENSHOT_CD, \
        VERIFYING, VERIFIED, VERIFY_TIPS, FOLLOW_MUTE, last_info

    a = json.loads(message)
    if "notice_type" in a:
        if "sub_type" in a:
            logging.debug(
                f"WS_Message post_type:{a['post_type']} notice_type:{a['notice_type']} sub_type:{a['sub_type']}")
        else:
            logging.debug(f"WS_Message post_type:{a['post_type']} notice_type:{a['notice_type']}")
    else:
        logging.debug(f"WS_Message post_type:{a['post_type']}")

    if a["post_type"] == "notice" and a["notice_type"] == "notify" and a["sub_type"] == "poke" and "group_id" in a and \
            a["target_id"] == a["self_id"]:
        sendMessage(random.choice(
            ["不要戳我啦 =w=", "不要动我!", "唔...", "Hentai!", "再戳...会...会变奇怪的..", "啊啊啊不要再戳我辣!!!", "好痛! 呜~", "Nya~"]),
            target_group=a["group_id"], target_qq=a["user_id"])
        sendMessage(f"[CQ:poke,qq={a['user_id']}]", target_group=a["group_id"])

    if a["post_type"] == "request" and a["request_type"] == "friend":
        sendMessage("[Friend Request]\nID:" + str(a["user_id"]) + "\nComment:" + str(
            a["comment"] + "\n如需通过输入!invi friend agree " + str(a["flag"])), target_group=1019068934)
    #        data1 = {
    #            "flag": a["flag"],
    #            "approve": True
    #        }
    #        post2http("/set_friend_add_request", data=data1)

    if a["post_type"] == "request" and a["request_type"] == "group" and a["sub_type"] == "invite":
        sendMessage("[Group Request]\nID:" + str(a["user_id"]) + "\nComment:" + str(
            a["comment"] + "\n如需通过输入!invi group agree " + str(a["flag"])), target_group=1019068934)
    #        data1 = {
    #            "flag": a["flag"],
    #            "type": "invite",
    #            "approve": True
    #        }
    #        post2http("/set_group_add_request", data=data1)

    try:
        if a["post_type"] == "notice" and a["notice_type"] == "group_ban":
            if a["sub_type"] == "ban":
                sendMessage(
                    f"[CQ:at,qq={a['user_id']}]从 [CQ:at,qq={a['operator_id']}]那获得了时长为 {get_lapsetime(a['duration'])} 的禁言",
                    target_group=a["group_id"])

            #                if a['user_id'] == a['self_id']:
            #                   data1 = {
            #                      "group_id": a['group_id']
            #                 }
            #                post2http("/set_group_leave", data=data1)
            #
            #                   sendMessage(f"机器人在群 {a['group_id']} 被禁言 已自动退出", target_group=1019068934)

            if a["sub_type"] == "lift_ban":
                sendMessage(
                    f"[CQ:at,qq={a['user_id']}]从 [CQ:at,qq={a['operator_id']}]那获得了解除禁言",
                    target_group=a["group_id"])
    except Exception as e:
        logging.warning("\n".join(traceback.format_exception(e)))

    msg = Message(message)

    try:
        # 处理消息内容

        if msg.text == "":
            return

        if msg.id in CACHE_MESSAGE and msg.id != -1:
            if len(CACHE_MESSAGE) >= 1000:
                CACHE_MESSAGE.clear()
            return
        else:
            CACHE_MESSAGE.append(msg.id)

        if time.time() - MESSAGE_PRE_MINUTE[0] >= 60:
            MESSAGE_PRE_MINUTE = [time.time(), 1]
        else:
            MESSAGE_PRE_MINUTE[1] += 1
        ALL_MESSAGE += 1

        # Call Event
        if moduleManager.process_event(GroupMessageEvent(msg)):
            msg.recall()

        command_list = msg.text.split(" ")

        logging.info("[{0}] {1}({2}) {3}".format(msg.group.id, msg.sender.name, msg.sender.id, msg.text))

        if msg.text in ["!help", "菜单"]:
            msg.fast_reply(
                f"请访问: https://lingbot.guimc.ltd/\nLingbot官方群: https://t.me/LingBotProject\n本群验证状态:{msg.group.verify_info()}")

#         if command_list[0] == "!mail":
#             msg.group.id = str(msg.group.id)
#             if len(command_list) == 1:
#                 msg.fast_reply("""邮箱验证指令:
# 开始验证: !mail verify 邮箱地址
# 完成验证: !mail code 验证码
# 移除验证: !mail reset 本群群号
# 查看本群验证状态: !help""")
#             if command_list[1] == "verify":
#                 if msg.group.id in VERIFIED:
#                     msg.fast_reply("本群已经验证过了! 输入 !help 可以查询激活状态")
#
#                 if msg.group.id not in VERIFYING:
#                     VERIFYING[msg.group.id] = {
#                         "time": 0,
#                         "code": "",
#                         "user": 0,
#                         "mail": ""
#                     }
#
#                 if time.time() - float(VERIFYING[msg.group.id]["time"]) < 300:
#                     msg.fast_reply(
#                         "已经有人发起了一个验证消息了! 请等待: {}s".format(300 - (time.time() - float(VERIFYING[msg.group.id]["time"]))))
#                     return
#
#                 print(a["sender"]["role"])
#
#                 if a["sender"]["role"] == "member" and not msg.sender.isadmin():
#                     msg.fast_reply("目前不支持普通群成员发起验证!")
#                     return
#
#                 VERIFYING[msg.group.id]["mail"] = command_list[2]
#                 VERIFYING[msg.group.id]["user"] = msg.sender.id
#                 VERIFYING[msg.group.id]["code"] = str(random.randint(100000000, 999999999))
#                 VERIFYING[msg.group.id]["time"] = time.time()
#                 send_email(command_list[2], f"[LingBot Team] 群{msg.group.id} - 激活", f"""您好, {msg.sender.name}:
# \t感谢您使用 LingBot 机器人, 您正在尝试给群 {msg.group.id} 激活! 您的验证码是: {VERIFYING[msg.group.id]["code"]}
# \t请您在群内使用指令 !mail code {VERIFYING[msg.group.id]["code"]} 来激活
# \t此验证码 30 分钟内有效
# \t如果您没不知道这是, 请忽略此邮件
# """)
#                 msg.fast_reply("我们已经尝试发送一封电子邮件到您的邮箱 请按照邮件内容操作")
#
#             if command_list[1] == "code":
#                 if msg.group.id not in VERIFYING:
#                     msg.fast_reply("没有查到本群的激活信息!")
#                 elif time.time() - VERIFYING[msg.group.id]["time"] >= 1800:
#                     msg.fast_reply("""本群的验证码已经过期了!
# 邮箱验证指令:
# 开始验证: !mail verify 邮箱地址
# 完成验证: !mail code 验证码
# 查看本群验证状态: !help""")
#                 elif str(command_list[2]) == VERIFYING[msg.group.id]["code"]:
#                     msg.fast_reply("激活成功!")
#                     VERIFIED[msg.group.id] = VERIFYING[msg.group.id]["mail"]
#                     del VERIFYING[msg.group.id]
#                 else:
#                     msg.fast_reply("我们在处理您的验证时出现了亿点问题 请检查激活码是否正确")
#
#             if command_list[1] == "reset" and not a["sender"]["role"] == "member":
#                 if msg.group.id not in VERIFIED:
#                     msg.fast_reply("本群并没有验证过!")
#                 try:
#                     if command_list[2] + command_list[3] == f"{msg.group.id}{VERIFIED[msg.group.id]}" and command_list[
#                         4] == "我知道我在做什么!":
#                         del VERIFIED[msg.group.id]
#                         msg.fast_reply("本群验证信息已经移除!")
#                         return
#                     else:
#                         msg.fast_reply("你只能移除这个群的验证信息!")
#                         return
#                 except:
#                     msg.fast_reply("请正确使用!mail reset <当前群号> <当前验证邮箱> 我知道我在做什么! 来移除本群的验证信息!")

        if command_list[0] == "!leave":
            try:
                data1 = {
                    "group_id": int(command_list[1])
                }
                post2http("/set_group_leave", data=data1)
                msg.fast_reply("已尝试在" + command_list[1] + "退出")
            except:
                msg.fast_reply("Error")

        if command_list[0] == "!invitations" or command_list[0] == "!invi":
            if msg.sender.isadmin():
                if command_list[1] == "group":
                    if command_list[2] == "agree":
                        try:
                            data1 = {
                                "flag": command_list[3],
                                "type": "invite",
                                "approve": True
                            }
                            post2http("/set_group_add_request", data=data1)
                        except:
                            msg.fast_reply("无flag")
                    if command_list[2] == "refuse":
                        try:
                            data1 = {
                                "flag": command_list[3],
                                "type": "invite",
                                "approve": False
                            }
                        except:
                            msg.fast_reply("无flag")
                if command_list[1] == "friend":
                    if command_list[2] == "agree":
                        try:
                            data1 = {
                                "flag": command_list[3],
                                "approve": True
                            }
                            post2http("/set_friend_add_request", data=data1)
                        except:
                            msg.fast_reply("无flag")
                    if command_list[2] == "refuse":
                        if command_list[2] == "agree":
                            try:
                                data1 = {
                                    "flag": command_list[3],
                                    "approve": False
                                }
                                post2http("/set_friend_add_request", data=data1)
                            except:
                                msg.fast_reply("无flag")
            else:
                msg.fast_reply("您还没有权限做这件事哦")

        if command_list[0] == "!runas":
            if msg.sender.isadmin():
                atcq = re.search(r'\[CQ:at,qq=(.*)]', command_list[1])
                if atcq is not None:
                    command_list[1] = command_list[1].replace("[CQ:at,qq={}]".format(atcq.group(1)), str(atcq.group(1)))
                data1 = {
                    "post_type": "message",
                    "message_type": "group",
                    "message": " ".join(command_list[2:]),
                    "sender": {
                        "user_id": int(command_list[1]),
                        "nickname": "FakeMessage"
                    },
                    "group_id": msg.group.id,
                    "message_id": -1
                }
                on_message2(ws, json.dumps(data1))

        if msg.text in ["!restart", "!quit", "!reload"] and msg.sender.isadmin():
            msg.fast_reply("Restarting...")
            print(requests.get("http://" + HTTPURL + "/set_restart").text)
            stop()

        #         if not msg.group.isverify():
        #             return
        try:
            if FOLLOW_MUTE[str(msg.sender.id)] > time.time():
                msg.recall().mute(int(FOLLOW_MUTE[str(msg.sender.id)] - time.time()))
        except:
            pass
        if msg.id != -1:
            if msg.sender.id not in SPAM2_MSG:
                _temp = Message()
                _temp.text = "¶¶¶¶" * 10086
                SPAM2_MSG[msg.sender.id] = _temp  # msg.text
                SPAM2_MESSAGE_LIST[msg.sender.id] = []
                SPAM2_VL[msg.sender.id] = 0
            _simhash_dis = simhash_similarity(str(SPAM2_MSG[msg.sender.id].text).lower(), msg.text.lower())
            if _simhash_dis >= 0.836:
                SPAM2_VL[msg.sender.id] += 12.5 * (_simhash_dis - 0.5) + (len(msg.text) * 0.05)  # :10
                if _simhash_dis >= 0.99:
                    SPAM2_VL[msg.sender.id] += 10

                if SPAM2_VL[msg.sender.id] >= 55:
                    # if msg.sender.isadmin():
                    #     sendMessage(
                    #         f"{msg.sender.id}发送的一条消息疑似重复, 且此人在超管名单内\n上一条内容: \n {SPAM2_MSG[msg.sender.id]}\n内容:\n{msg.text}\n相似度: {_simhash_dis}\nVL: {SPAM2_VL[msg.sender.id]}",
                    #         target_group=1019068934)
                    # msg.recall()
                    if SPAM2_VL[msg.sender.id] >= 100:
                        msg.recall()
                        # 消息的群组去重
                        _temp = []
                        _tmp2 = []
                        for j in SPAM2_MESSAGE_LIST[msg.sender.id]:
                            if str(j.group.id) in _tmp2:
                                continue
                            _tmp2.append(str(j.group.id))
                            _temp.append(j)
                        # 先分别禁言
                        for _ in _temp:
                            _.mute(86400)
                            time.sleep(random.randint(250, 1500) / 1000)

                        # 再撤回
                        while len(SPAM2_MESSAGE_LIST[msg.sender.id]) > 0:
                            SPAM2_MESSAGE_LIST[msg.sender.id].pop(0).recall()
                            time.sleep(random.randint(250, 2000) / 1000)

                        msg.mute(43199 * 60)  # 43199 * 60 # :259200
                        SPAM2_VL[msg.sender.id] -= 20
                        del _temp, _tmp2
                        SPAM2_MESSAGE_LIST[msg.sender.id].clear()
                        return
                    # else:
                    #     msg.mute(600)
                    # msg.fast_reply("您貌似在刷屏/群发?", reply=False)
                    # return

                    if len(SPAM2_MESSAGE_LIST[msg.sender.id]) >= 20:
                        SPAM2_MESSAGE_LIST[msg.sender.id].pop(0)

                for i in SPAM2_MESSAGE_LIST[msg.sender.id]:
                    _sim = simhash_similarity(str(i.text).lower(), msg.text.lower())
                    if _sim > 0.9:
                        SPAM2_VL[msg.sender.id] += _sim
                SPAM2_MESSAGE_LIST[msg.sender.id].append(msg)
                SPAM2_MSG[msg.sender.id] = msg
            else:
                SPAM2_MSG[msg.sender.id] = msg
                if SPAM2_VL[msg.sender.id] > 0:
                    SPAM2_VL[msg.sender.id] -= 2.5 * (0.9 - _simhash_dis)  # :2

            reScan = re.findall(
                ANTI_AD,
                msg.text.replace(" ", "").replace(".", "").replace("\n", "").lower())
            if len(msg.text) >= 33 and len(reScan) >= 2:
                SPAM2_VL[msg.sender.id] += 4
                if msg.sender.isadmin():
                    sendMessage("{}发送的一条消息触发了正则 并且此人在超管名单内\n内容:\n{}".format(msg.sender.id, msg.text),
                                target_group=1019068934)
                    return
                msg.mute(3600).recall()
                ALL_AD += 1
                return

            # Bug: 名称有缓存

            # sc_id_ad = re.search(ANTI_AD, msg.sender.name.replace(" ", "").replace(".", "").replace("\n", "").lower())
            # if sc_id_ad is not None and not msg.sender.isadmin():
            #     msg.mute(600)
            #     msg.recall()
            #     time.sleep(random.randint(500, 2000) / 1000)
            #     msg.fast_reply("您的名称中似乎存在广告", reply=False)
            #     ALL_AD += 1
            #     return

            scan_lv = msg_scanner.predict(msg.text_nocq)
            if scan_lv >= 0.8:
                msg.fast_reply(f"您的消息貌似有违法内容?\nLevel: {round(scan_lv, 3)}", reply=False)
                if scan_lv >= 0.9:
                    msg.recall().mute(600)

            if len(msg.text) > 1500:
                msg.mute(600).recall().fast_reply("消息太长了哟", reply=False)
                SPAM2_VL[msg.sender.id] += 3
                return

            multiMsg = re.search(r'\[CQ:forward,id=(.*)]', msg.text)
            if multiMsg is not None:
                a = \
                    requests.get(
                        url="http://" + HTTPURL + "/get_forward_msg?message_id=" + str(multiMsg.group(1))).json()[
                        "data"]["messages"]
                multiMsg_raw = ""
                for i in a:
                    multiMsg_raw += i["content"]
                reScan = re.search(
                    ANTI_AD,
                    multiMsg_raw.replace(" ", "").replace(".", "").replace("\n", "").lower())
                if reScan is not None:
                    msg.fast_reply("您发送的合并转发内容貌似有广告!", reply=False).mute(3600).recall()
                    ALL_AD += 1
                    SPAM2_VL[msg.sender.id] += 3
                    return

            try:
                if spammer_checker(msg):
                    msg.mute(60).recall().fast_reply("您的说话速度有点快，是不是在刷屏呢？", reply=False)
            except:
                pass

            if msg.sender.id in BLACK_LIST:
                msg.mute(60)
                msg.recall()
                return

            if msg.text.count("[CQ:image") >= 3:
                if msg.sender.isadmin() is False:
                    msg.mute(60).recall().fast_reply("太...太多图片了..", reply=False)
                    return

        if (msg.group.id, msg.sender.id) in REPEATER:
            if not (command_list[0] == "!repeater" and (command_list[1] == "add" or command_list[1] == "remove")):
                msg.fast_reply(msg.text, reply=False, at=False)
        try:
            if str(msg.group.id) not in MESSAGE_COUNTER:
                MESSAGE_COUNTER[str(msg.group.id)] = {}
            if str(msg.sender.id) not in MESSAGE_COUNTER[str(msg.group.id)]:
                MESSAGE_COUNTER[str(msg.group.id)][str(msg.sender.id)] = 0
            MESSAGE_COUNTER[str(msg.group.id)][str(msg.sender.id)] += 1
        except:
            pass

        if msg.text in ["!test", "凌状态"]:
            msg.fast_reply(
                f"Hello! 已处理 {ALL_MESSAGE} 条消息\n"
                f"已经运行了 {get_runtime()}\n"
                f"平均每条消息耗时 {timePreMessage} 秒\n"
                f"拦截了 {ALL_AD} 条广告 占全部处理消息的 {(ALL_AD / ALL_MESSAGE) * 100}%\n"
                f"目前有 {threading.active_count()} 个线程正在运行"
            )

        if msg.text == "一语":
            msg.fast_reply(requests.get("http://api.muxiuge.cn/API/society.php").json()["text"])

        if msg.text == "!testzb":
            if SCREENSHOT_CD + 60 <= time.time():
                msg.fast_reply("Trying...")
                goodmor(msg.group.id)
                SCREENSHOT_CD = time.time()
            else:
                msg.fast_reply("Too fast!")

        # if msg.text == "!hyp":
        # msg.fast_reply("Test Hypixel-Apikey .ing")
        # return

        if command_list[0] == "!丢":
            # 图片/灵感来源: https://github.com/MoeMegu/ThrowIt-Mirai
            # 图片文件: r2gac549.bmp
            atcq = re.search(r'\[CQ:at,qq=(.*)]', msg.text)
            if atcq is not None:
                command_list = msg.text.replace("[CQ:at,qq={}]".format(atcq.group(1)), str(atcq.group(1))).replace("me",
                                                                                                                   str(msg.sender.id)).split(
                    " ")
            tx_image = requests.get(url=f"http://qlogo4.store.qq.com/qzone/{command_list[1]}/{command_list[1]}/100")
            ima = Image.open(BytesIO(tx_image.content))
            ima = ima.resize((136, 136), Image.ANTIALIAS)
            imc = Image.open("r2gac549.bmp")
            imb, mask1 = mask_circle_transparent(ima.rotate(-160), 0, 2)
            imc.paste(imb, (19, 181), mask=mask1)
            _temp = BytesIO()
            imc.save(_temp, format="PNG")
            msg.fast_reply("[CQ:image,file=base64://{}]".format(base64.b64encode(_temp.getvalue()).decode()))

        if command_list[0] == "!music":
            # Netease API: http://cloud-music.pl-fe.cn/search?keywords={" ".join(command_list[1:])}
            search_result = requests.get(
                url=f'http://cloud-music.pl-fe.cn/search?keywords={" ".join(command_list[1:])}').json()
            if search_result["code"] != 200:
                msg.fast_reply(f"搜索失败! {search_result['code']}")
                return

            msg.fast_reply("这是你要找的歌吗?").fast_reply(
                f"[CQ:music,type=163,id={search_result['result']['songs'][0]['id']}]")

        if command_list[0] == "!5k":
            # 图片/灵感来源: https://github.com/SAGIRI-kawaii/saya_plugins_collection/tree/master/modules/5000zhao
            # 字体文件: ./5k_fonts
            if len(command_list[1]) >= 18 or len(command_list[2]) >= 18:
                msg.fast_reply("内容过长 被拒绝运行")
                return
            imageuid = str(random.randint(10000000, 9999999999))
            five_k_utils.genImage(word_a=command_list[1], word_b=command_list[2]).save(imageuid + ".cache.png")
            with open(imageuid + ".cache.png", "rb") as f:
                msg.fast_reply("[CQ:image,file=base64://{}]".format(base64.b64encode(f.read()).decode()))

        if msg.text == "!random":
            msg.fast_reply(str(random.randint(1, 100)))
            return

        if command_list[0] == "!testchrome" and msg.sender.id == 1584784496:
            msg.fast_reply("Trying...") \
                .fast_reply("[CQ:image,file=base64://{}]".format(
                requests.post(url="http://localhost:25666/url2base64",
                              data={"url": " ".join(command_list[1:])}).text.replace("\n", "")
            )
            )

        if msg.text.find("[CQ:json,data=") != -1:
            msg.text = msg.text.replace("\\", "")
            if msg.text.find('https://b23.tv/') != -1:
                try:
                    str1 = requests.get(url="https://api.bilibili.com/x/web-interface/view?bvid={}".format(
                        re.findall(
                            r'<link data-vue-meta="true" rel="canonical" href="https://www.bilibili.com/video/.*/">',
                            requests.get(json.loads(
                                re.search(r"\[CQ:json,data=(.*)]", msg.text).group(1).replace("&amp;", "&").replace(
                                    "&#44;", ","))[
                                             "meta"]["news"]["jumpUrl"]).text)[0].replace(
                            r'<link data-vue-meta="true" rel="canonical" href="https://www.bilibili.com/video/', "")[
                        :-3])).json()
                except KeyError:
                    str1 = requests.get(url="https://api.bilibili.com/x/web-interface/view?bvid={}".format(
                        re.findall(
                            r'<link data-vue-meta="true" rel="canonical" href="https://www.bilibili.com/video/.*/">',
                            requests.get(json.loads(
                                re.search(r"\[CQ:json,data=(.*)]", msg.text).group(1).replace("&amp;", "&").replace(
                                    "&#44;", ","))[
                                             "meta"]["detail_1"]["qqdocurl"]).text)[0].replace(
                            r'<link data-vue-meta="true" rel="canonical" href="https://www.bilibili.com/video/', "")[
                        :-3])).json()

                if str1["code"] != 0:
                    logging.warning("查询失败")
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
                    msg.fast_reply("[CQ:image,file=base64://" + base64.b64encode(f.read()).decode() + "]")

        if msg.text == "一英":
            msg.fast_reply(requests.get("http://open.iciba.com/dsapi/").json()["content"] + "\n" +
                           requests.get("http://open.iciba.com/dsapi/").json()["note"])

        if msg.text == "二次元":
            msg.fast_reply("[CQ:image,file=base64://" + acg_img() + "]")

        if msg.text == "必应壁纸":
            msg.fast_reply("[CQ:image,file=base64://" + base64.b64encode(
                requests.get("http://www.xgstudio.xyz/api/bing.php").content).decode() + "]")

        if msg.text == "一话":
            req1 = requests.get("http://open.iciba.com/dsapi/").json()
            msg.fast_reply(requests.get("http://api.muxiuge.cn/API/society.php").json()["text"]) \
                .fast_reply(req1["content"] + "\n" + req1["note"])

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
                    temp_msg += "{}: {} ({}%)\n".format(temp_list[i][0], _all_players[i],
                                                        round((_all_players[i] / _all_player) * 100, 2))
                except Exception as e:
                    logging.error(e)
            logging.debug(temp_msg)
            msg.fast_reply("[CQ:image,file=base64://{}]".format(text2image(temp_msg)))
            return
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

        if command_list[0] == "!plus":
            msg.fast_reply(str(float(command_list[1]) + float(command_list[2])))
            return
        if command_list[0] == "!subtract":
            msg.fast_reply(str(float(command_list[1]) - float(command_list[2])))
            return
        if command_list[0] == "!multiply":
            msg.fast_reply(str(float(command_list[1]) * float(command_list[2])))
            return
        if command_list[0] == "!divide":
            if int(command_list[2]) == 0:
                msg.fast_reply("零不能作除数哦~")
                return
            msg.fast_reply(str(float(command_list[1]) / float(command_list[2])))
            return

        if command_list[0] == "!tcping":
            if len(command_list) == 1:
                msg.fast_reply("语法错误 使用方法为: !tcping IP[:端口(默认为80)]\n如: !tcping api.github.com:80")
            else:
                try:
                    msg.fast_reply("正在进行TCPing")
                    _host = ""
                    _port = "80"
                    if command_list[1].find(":") != -1:
                        _host, _port = command_list[1].split(":")
                    else:
                        _host = command_list[1]

                    _ping = tcping.Ping(_host, int(_port), 1.0)
                    _ping.ping(5)
                    msg.fast_reply(
                        "[CQ:image,file=base64://{}]".format(text2image(_ping.result.raw.replace(", ", "\n"))))
                except:
                    msg.fast_reply("无法获取信息")
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
                atcq = re.search(r'\[CQ:at,qq=(.*)]', msg.text)
                if atcq is not None:
                    command_list = msg.text.replace("[CQ:at,qq={}]".format(atcq.group(1)), str(atcq.group(1))).split(
                        " ")
                command_list[2] = int(command_list[2].replace("@", ""))
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
                atcq = re.search(r'\[CQ:at,qq=(.*)]', msg.text)
                if atcq is not None:
                    command_list = msg.text.replace("[CQ:at,qq={}]".format(atcq.group(1)), str(atcq.group(1))).split(
                        " ")
                command_list[2] = int(command_list[2].replace("@", ""))
                if int(command_list[2]) not in BLACK_LIST:
                    msg.fast_reply("黑名单内没有这个人")
                    return
                BLACK_LIST.remove(int(command_list[2]))
                msg.fast_reply("操作成功")

        if command_list[0] == "!mcping":
            try:
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
                    aaa = aaa + "\n[CQ:image,file=" + server.favicon.replace("data:image/png;base64,",
                                                                             "base64://") + "]"
                msg.fast_reply(aaa)
            except:
                msg.fast_reply("无法获取信息")

        if command_list[0] == "!hypban":
            msg.fast_reply("本功能已经停止使用了")
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
                if command_list[1] == "all":
                    s = getGroups()
                    msg.fast_reply("正在群发... 目标:{}个群".format(len(s)))
                    _prefix = "(由 {}({}) 发起的群发消息)\n".format(msg.sender.name, msg.sender.id)
                    for i in s:
                        if i not in IGNORE_GROUP:
                            nowmsg = ""
                            for i2 in list(msg1):
                                nowmsg += i2 + random.choice(["\u202D", "", "", "", ""])
                            sendMessage(_prefix + nowmsg, target_group=i)
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

        if (msg.group.id, msg.sender.id) in AUTISM:
            AUTISM.remove((msg.group.id, msg.sender.id))
            if command_list[0] == "0" or "不想自闭" in command_list[0]:
                msg.fast_reply("那就别自闭了")
            else:
                command_list[0] = int(command_list[0])
                mute_time = command_list[0] * 60
                time_type = 'min'
                if len(command_list) > 1:
                    if command_list[1] == 's' or command_list[1] == '秒':
                        time_type = 's'
                        mute_time = command_list[0]
                    if command_list[1] == 'h' or command_list[1] == '小时':
                        time_type = 'h'
                        mute_time = command_list[0] * 3600
                    if command_list[1] == 'd' or command_list[1] == '天':
                        time_type = 'd'
                        mute_time = command_list[0] * 86400
                mutePerson(msg.group.id, msg.sender.id, mute_time)
                msg.fast_reply(f"您将要自闭{command_list[0]}{mute_type(time_type)}")

        if command_list[0] == "!我要自闭":
            if len(command_list) == 1:
                sendMessage("您想自闭多久呢？", msg.sender.id, msg.group.id)
                AUTISM.append((msg.group.id, msg.sender.id))
            else:
                if command_list[1] == "help":
                    sendMessage("""
自闭指令 : !我要自闭
使用方法 :
    发送“!我要自闭 <时间> <单位>”
使用方法② : 
    发送”!我要自闭“
    然后再发送”<时间> <单位>“
<单位> : 默认是分钟，可填 s (秒)、 h (时)、 d (天)
        发送 0 或包含 “不想自闭” 可取消自闭
                    """, target_group=msg.group.id)
                    return
                command_list[1] = int(command_list[1])
                mute_time = command_list[1] * 60
                time_type = 'min'
                if len(command_list) > 2:
                    if command_list[2] == 's' or command_list[2] == '秒':
                        time_type = 's'
                        mute_time = command_list[1]
                    if command_list[2] == 'h' or command_list[2] == '小时':
                        time_type = 'h'
                        mute_time = command_list[1] * 3600
                    if command_list[2] == 'd' or command_list[2] == '天':
                        time_type = 'd'
                        mute_time = command_list[1] * 86400
                mutePerson(msg.group.id, msg.sender.id, mute_time)
                msg.fast_reply(
                    f"您将要自闭{command_list[1]}{mute_type(time_type)}")

        if command_list[0] == "!vl":
            if not msg.sender.isadmin():
                msg.fast_reply("你的权限不足!")
                return
            if command_list[1] == "spam2":
                if len(command_list) < 3:
                    msg.fast_reply(f'spam2 vl {json.dumps(SPAM2_VL)}')
                    return
                else:
                    msg.fast_reply(f'此人spam2 vl为 {SPAM2_VL[int(command_list[2])]}')
                    return
            elif command_list[1] == "spam":
                msg.fast_reply(f"此群成员spam vl为 {int(ANTISPAMMER[command_list[2]])}")
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

        #         if command_list[0] == "!fdpinfo":
        #             if command_list[1] == "online":
        #                 url = "https://bstats.org/api/v1/plugins/11076/charts/minecraftVersion/data"
        #                 a = requests.get(url=url).json()
        #                 onlinePlayer = 0
        #                 for i in a:
        #                     onlinePlayer += i["y"]
        #                 msg.fast_reply("[CQ:image,file=base64://" + text2image("OnlinePlayers: {}".format(onlinePlayer)) + "]")
        #             elif command_list[1] == "versions":
        #                 url = "https://bstats.org/api/v1/plugins/11076/charts/pluginVersion/data"
        #                 a = requests.get(url=url).json()
        #                 onlineVersion = []
        #                 for i in a:
        #                     onlineVersion.append("{}: {}".format(i["name"], i["y"]))
        #                 msg.fast_reply("[CQ:image,file=base64://" + text2image(
        #                     "OnlineVersionsInfo:\n{}".format("\n".join(onlineVersion))) + "]")
        #             elif command_list[1] == "systems":
        #                 url = "https://bstats.org/api/v1/plugins/11076/charts/os/data"
        #                 a = requests.get(url=url).json()
        #                 onlineSystem = []
        #                 for i in a["seriesData"]:
        #                     onlineSystem.append("{}: {}".format(i["name"], i["y"]))
        #                 msg.fast_reply(
        #                     "[CQ:image,file=base64://" + text2image("OnlineSystms:\n{}".format("\n".join(onlineSystem))) + "]")
        #             elif command_list[1] == "countries":
        #                 url = "https://bstats.org/api/v1/plugins/11076/charts/location/data"
        #                 a = requests.get(url=url).json()
        #                 onlineCountry = []
        #                 for i in a:
        #                     onlineCountry.append("{}: {}".format(
        #                         i["name"].replace("Hong Kong", "Hong Kong, China").replace("Taiwan", "Taiwan, China"),
        #                         i["y"]))
        #                 msg.fast_reply("[CQ:image,file=base64://" + text2image(
        #                     "OnlineCountrys:\n{}".format("\n".join(onlineCountry))) + "]")
        #             elif command_list[1] == "beta":
        #                 msg.fast_reply("Please wait...")
        #                 url = "https://api.github.com/repos/UnlegitMC/FDPClient/actions/runs"
        #                 a = requests.get(url=url).json()
        #                 objectIDs = []
        #                 for i in a["workflow_runs"]:
        #                     if i["name"] == "build":
        #                         objectIDs.append(i["id"])
        #                 actionInfo = requests.get(
        #                     url="https://api.github.com/repos/UnlegitMC/FDPClient/actions/runs/{}".format(objectIDs[0])).json()
        #                 upd_time = actionInfo["head_commit"]["timestamp"]
        #                 updMsg = actionInfo["head_commit"]["message"]
        #                 updAuthor = "{} ({})".format(actionInfo["head_commit"]["author"]["name"],
        #                                              actionInfo["head_commit"]["author"]["email"])
        #                 msg.fast_reply("Update Time:{}\n"
        #                                "Update Message:{}\n"
        #                                "Author:{}\n"
        #                                "Download URL:https://nightly.link/UnlegitMC/FDPClient/actions/runs/{}/FDPClient.zip\n".format(
        #                     upd_time, updMsg, updAuthor, objectIDs[0]))
        #             elif command_list[1] == "release":
        #                 url = "https://api.github.com/repos/UnlegitMC/FDPClient/releases/latest"
        #                 a = requests.get(url=url).json()
        #                 files = []
        #                 for i in a["assets"]:
        #                     files.append(
        #                         "{}: {}".format(i["name"], i["browser_download_url"].replace("github.com", "hub.fastgit.org")))
        #                 msg.fast_reply("Version: {}\n".format(a["name"]) + "\n".join(files))
        if command_list[0] == "!hyp":
            if len(command_list) == 1:
                msg.fast_reply("格式貌似有点问题?\n访问 https://lingbot.guimc.ltd/#/Commands 找一找你想要的功能罢")
                return

            # 获取玩家信息
            try:
                player1 = hypixel.Player(command_list[1])
            except hypixel.PlayerNotFoundException:
                msg.fast_reply("貌似没有这个玩家?\n访问 https://lingbot.guimc.ltd/#/Commands 找一找你想要的功能罢")
                return
            pI = player1.getPlayerInfo()
            logging.debug(pI)
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
                    onlineMode = "Online: {} - {} ({})".format(_onlineStatus["gameType"], _onlineStatus["mode"],
                                                               _onlineStatus["map"])
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
                rank=player1.getRank()["rank"].replace(" PLUS", "+"),
                name=pI["displayName"],
                level=player1.getLevel(),
                karma=pI["karma"],
                last_login=datetime.datetime.utcfromtimestamp(pI["lastLogin"] / 1000).strftime("%Y-%m-%d %H:%M:%S"),
                first_login=datetime.datetime.utcfromtimestamp(pI["firstLogin"] / 1000).strftime("%Y-%m-%d %H:%M:%S"),
                onlineMode=onlineMode,
                lastLogout=datetime.datetime.utcfromtimestamp(lastLogout / 1000).strftime("%Y-%m-%d %H:%M:%S"))

            if playerSkin.status_code == 200:
                pmsg = "[CQ:image,file=base64://" + base64.b64encode(playerSkin.content).decode() + "]\n" + pmsg

            try:
                sbplayer = hypixel.getJSON('skyblock/profiles', uuid=pI['uuid'])
                try:
                    profile_id = sbplayer["profiles"][0]["profile_id"]
                    sbprofile = sbplayer["profiles"][0]["members"][profile_id]
                except:
                    profile_id = list(sbplayer["profiles"][0]["members"])[0][0]
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
                logging.error(traceback.format_exc())
            msg.fast_reply(pmsg)

        if msg.sender.id in INTRODUCE['waiting']:
            atcq = re.search(r'\[CQ:at,qq=(.*)]', msg.text)
            if atcq is not None:
                command_list = msg.text.replace("[CQ:at,qq={}]".format(atcq.group(1)), str(atcq.group(1))).split(
                    " ")
            INTRODUCE["waiting"].remove(msg.sender.id)
            if command_list[0].isdigit() or command_list[0] == 'me':
                if command_list[0] == 'me':
                    command_list[0] = str(msg.sender.id)
                if str(command_list[0]) in INTRODUCE['qq']:
                    if str(msg.group.id) in INTRODUCE['qq'][str(command_list[0])]:
                        sendMessage(f"的介绍为 : \n{INTRODUCE['qq'][str(command_list[0])][str(msg.group.id)]}",
                                    command_list[0], msg.group.id)
                    else:
                        sendMessage(f"未在此群添加介绍", command_list[0], msg.group.id)
                else:
                    sendMessage(f"未在任何群添加介绍", command_list[0], msg.group.id)
            else:
                msg.fast_reply("请发送QQ号或'me'!!!")
            return

        if command_list[0] == "!git":
            # 1.Github项目及API接口数据
            api = 'https://api.github.com/repos/LingBot-Project/LingBot'
            web_page = "https://github.com/LingBot-Project/LingBot"

            # 2.发送请求，获取数据
            all_info = requests.get(api).json()

            # 3.解析想要的数据，并打印
            cur_update = all_info['updated_at']

            if str(last_info) == str(cur_update):
                msg.fast_reply("无新Commit")
            else:
                msg.fast_reply("有新Commit,time:" + cur_update)
            last_info = str(cur_update)

        if command_list[0] == "!info":
            if msg.sender.isadmin:

                rt = threading.enumerate()
                cpu_usage = str(psutil.cpu_times_percent().user + psutil.cpu_times_percent().system)
                memory_usage = str(psutil.virtual_memory().percent)
                msg.fast_reply("CPU核心数量:" + str(
                    psutil.cpu_count()) + "核\n" + "CPU占用率:" + cpu_usage + "%\n内存占用率:" + memory_usage + "%\n运行中的Watchdog线程:" + str(
                    len(rt)))
                # msg.fast_reply("当前机器人运行状态:\nCPU: "+cpu_usage+"%\nMemory: "+memory_usage+"%\nRunning Threads: "+str(len(rt)))
            else:
                msg.fast_reply("您还没有权限哦")

        if command_list[0] == "!kick":
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
            kickdata1 = {
                "group_id": int(command_list[1]),
                "user_id": int(command_list[2]),
            }
            post2http(url="/set_group_kick", data=kickdata1)
            msg.fast_reply("已尝试在" + str(command_list[1]) + "移除" + str(command_list[2]))

        if command_list[0] == "!introduce" or command_list[0] == "!介绍":
            atcq = re.search(r'\[CQ:at,qq=(.*)]', msg.text)
            if atcq is not None:
                command_list = msg.text.replace("[CQ:at,qq={}]".format(atcq.group(1)), str(atcq.group(1))).split(
                    " ")
            introduce = msg.text
            if len(command_list) == 1:
                msg.fast_reply("您想看谁的介绍呢？")
                INTRODUCE['waiting'].append(msg.sender.id)
            elif command_list[1] == 'help':
                msg.fast_reply(f"""
介绍指令 : !introduce/!介绍
编辑介绍 :
    使用方法 :
        发送“!introduce/!介绍 <type> <群号> <介绍>”
    <type> : add(添加) remove(删除) edit(编辑)
    <群号> : 如果在本群可以填"this"
    <介绍> : 随便填（支持CQ码）
查看介绍 : 
    发送“!introduce/!介绍 <Q号>” 
    <Q号> : 填"me"介绍自己
超管功能 ： 
    可编辑某人的介绍
    使用方法 : !introduce/!介绍 edit_sb <Q号> <群号> <介绍>
""", reply=False, at=False)
            elif command_list[1] == "empty":
                if msg.sender.isadmin():
                    INTRODUCE["qq"] = {}
                    INTRODUCE["waiting"] = []
                    msg.fast_reply("已清空所有人的介绍")
                else:
                    msg.fast_reply("您的权限不足")
            elif len(command_list) == 2 and (command_list[1].isdigit() or command_list[1] == 'me'):
                if command_list[1] == 'me':
                    command_list[1] = str(msg.sender.id)
                if str(command_list[1]) in INTRODUCE['qq']:
                    if str(msg.group.id) in INTRODUCE['qq'][str(command_list[1])]:
                        sendMessage(f"的介绍为 : \n{INTRODUCE['qq'][str(command_list[1])][str(msg.group.id)]}",
                                    command_list[1], msg.group.id)
                    else:
                        sendMessage(f"未在此群添加介绍", command_list[1], msg.group.id)
                else:
                    sendMessage(f"未在任何群添加介绍", command_list[1], msg.group.id)
            elif len(command_list) >= 3:
                if command_list[2] == "this":
                    command_list[2] = str(command_list[2])
                if command_list[1] == "add":
                    if str(msg.sender.id) in INTRODUCE['qq']:
                        if str(msg.group.id) in INTRODUCE['qq'][str(msg.sender.id)]:
                            msg.fast_reply("您已经在这个群添加过介绍了，若要编辑请把add改为edit" if command_list[2] == str(
                                msg.group.id) else f"您已经在群{command_list[2]}添加过介绍了，")
                        else:
                            introduce = introduce.replace(f"{command_list[0]} {command_list[1]} ", '')
                            introduce = introduce.replace(f"{command_list[2]} ", '')
                            introduce = introduce.replace("this ", '')
                            INTRODUCE['qq'][str(msg.sender.id)][str(msg.group.id)] = introduce
                            msg.fast_reply("添加成功")
                    else:
                        INTRODUCE['qq'][str(msg.sender.id)] = {}
                        introduce = introduce.replace(f"{command_list[0]} {command_list[1]} ", '')
                        introduce = introduce.replace(f"{command_list[2]} ", '')
                        introduce = introduce.replace("this ", '')
                        INTRODUCE['qq'][str(msg.sender.id)][str(msg.group.id)] = introduce
                        msg.fast_reply("添加成功")
                if command_list[1] == "remove":
                    if str(msg.sender.id) in INTRODUCE['qq']:
                        if str(msg.group.id) in INTRODUCE['qq'][str(msg.sender.id)]:
                            del INTRODUCE['qq'][str(msg.sender.id)][str(msg.group.id)]
                            msg.fast_reply(
                                "已删除您在本群的介绍" if command_list[2] == str(msg.group.id) else f"已删除您在群{command_list[2]}的介绍")
                        else:
                            msg.fast_reply("您还未在此群添加介绍，请先把remove改为add添加后重试" if command_list[2] == str(
                                msg.group.id) else f"您还未在群{command_list[2]}添加介绍，请先把remove改为add添加后重试")
                    else:
                        msg.fast_reply("您还未在任何群添加介绍，请先把remove改为add添加后重试")
                if command_list[1] == "edit":
                    if str(msg.sender.id) in INTRODUCE['qq']:
                        if str(msg.group.id) in INTRODUCE['qq'][str(msg.sender.id)]:
                            introduce = introduce.replace(f"{command_list[0]} {command_list[1]} ", '')
                            introduce = introduce.replace(f"{command_list[2]} ", '')
                            introduce = introduce.replace("this ", '')
                            INTRODUCE['qq'][str(msg.sender.id)][str(msg.group.id)] = introduce
                            msg.fast_reply(
                                "已修改您在本群的介绍" if command_list[2] == str(msg.group.id) else f"已修改您在群{command_list[2]}的介绍")
                        else:
                            msg.fast_reply("您还未在此群添加介绍,请把edit改为add重试" if command_list[2] == str(
                                msg.group.id) else f"您还未在群{command_list[2]}添加介绍,请把edit改为add重试")
                    else:
                        msg.fast_reply("您还未在任何群添加介绍")
                if command_list[1] == "edit_sb":
                    if msg.sender.isadmin():
                        if command_list[3] == "this":
                            command_list[3] = str(msg.group.id)
                        introduce = introduce.replace(f"{command_list[0]} {command_list[1]} {command_list[2]} ", '')
                        introduce = introduce.replace(f"{command_list[3]} ", '')
                        introduce = introduce.replace("this ", '')
                        if command_list[2] not in INTRODUCE["qq"]:
                            INTRODUCE["qq"][command_list[2]] = {}
                        if int(command_list[2]) not in ADMIN_LIST:
                            INTRODUCE["qq"][command_list[2]][command_list[3]] = introduce
                            msg.fast_reply(f"已修改{command_list[2]}在本群的介绍" if command_list[3] == str(
                                msg.group.id) else f"已修改{command_list[2]}在群{command_list[3]}的介绍")
                        else:
                            msg.fast_reply("不可编辑超管的介绍！！")
                    else:
                        msg.fast_reply("权限不足！！")

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
                        command_list = msg.text.replace("[CQ:at,qq={}]".format(atcq.group(1)),
                                                        str(atcq.group(1))).split(" ")
                    for aclist in ACCOMPLISHMENT["qq"][command_list[2]]:
                        acmsg += f'[CQ:image,file={ACCOMPLISHMENT["ACCOMPLISHMENT"][aclist]}]'
                    msg.fast_reply("您获得的成就有\n" + acmsg)
            elif command_list[1] == "empty":
                ACCOMPLISHMENT["qq"][str(msg.sender.id)] = []
                msg.fast_reply("已清空您的成就")

        if re.search(r"我是傻逼|我是傻子|i am stupid|i'm stupid|i'm a fool|i‘m an idiot|i am a fool|i am an idiot", msg.text):
            add_achievements(str(msg.sender.id), msg, 'i_m_stupid')

        if command_list[0] == "!fmute":
            if command_list[1] == "list":
                msg.fast_reply(f"FOLLOW_MUTE: {FOLLOW_MUTE}")

            if not msg.sender.isadmin():
                msg.fast_reply("Hey! You don't have permission to do it!")
                return

            FOLLOW_MUTE[str(command_list[1])] = str(int(time.time()) + (int(command_list[2]) * 60))
            msg.fast_reply(
                f'Success!\nEnded Time:{datetime.datetime.utcfromtimestamp(int(FOLLOW_MUTE[str(command_list[1])])).strftime("%Y-%m-%d %H:%M:%S")}')

        if command_list[0] == "!testcounter":
            msg_counter_send(msg.group.id)

        if command_list[0] == "没什么卵用的测试":
            time_1 = datetime.datetime.strptime(str(datetime.datetime.now().date()) + '0:00', '%Y-%m-%d%H:%M')
            time_2 = datetime.datetime.strptime(str(datetime.datetime.now().date()) + '4:00', '%Y-%m-%d%H:%M')
            time_n = datetime.datetime.now()
            if time_1 <= time_n < time_2:
                pass

    except Exception as e:
        a = traceback.format_exc()
        logging.error(a)
        msg.fast_reply(
            "很抱歉，我们在执行你的指令时出现了一个问题 =_=\n各指令用法请查看 https://lingbot.guimc.ltd/\n[CQ:image,file=base64://{}]".format(
                text2image(a)))


def add_achievements(qq, msg, achievements):
    if qq not in ACCOMPLISHMENT["qq"]:
        ACCOMPLISHMENT["qq"][qq] = [achievements]
        msg.fast_reply(f'恭喜你获得了一个成就！！\n[CQ:image,file={ACCOMPLISHMENT["ACCOMPLISHMENT"][achievements]}]')
    elif achievements not in ACCOMPLISHMENT["qq"][qq]:
        ACCOMPLISHMENT["qq"][qq].append(achievements)
        msg.fast_reply(f'恭喜你获得了一个成就！！\n[CQ:image,file={ACCOMPLISHMENT["ACCOMPLISHMENT"][achievements]}]')


def mutePerson(group, qq_number, mute_time):
    if mute_time > (43199 * 60):
        mute_time = 43199 * 60
    data1 = {
        "group_id": int(group),
        "user_id": int(qq_number),
        "duration": int(mute_time)
    }
    post2http(url="/set_group_ban", data=data1)


def unmutePerson(group, qq_number):
    mutePerson(group, qq_number, 0)


def recall(msg_id):
    if msg_id == 0 | msg_id == -1:
        return
    data1 = {
        "message_id": int(msg_id)
    }
    post2http(url="/delete_msg", data=data1)


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
        s = post2http(url="/send_group_msg", data=data1)
        if not s.ok:
            # 如果请求失败
            s.raise_for_status()
    else:
        logging.warning("目前暂时不支持发送私聊消息")


def urlget(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 4 Build/JOP40D) AppleWebKit/535.19 (KHTML, '
                      'like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19'}
    temp = requests.get(url, headers=headers)
    return temp.text


def sendTempMsg(target1, target2, text):
    # 会风控
    logging.info(text)


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
        logging.debug(a.json()["data"])
        for i in a.json()["data"]:
            groups.append(i["group_id"])
        return groups


def permCheck(groupID, target):
    return True


def mute_type(mute__type):
    if mute__type == "s":
        return "秒"
    if mute__type == "min":
        return "分钟"
    if mute__type == "h":
        return "小时"
    if mute__type == "d":
        return "天"


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
    sfl_time = b - a
    if timePreMessage == 0:
        timePreMessage = sfl_time
    else:
        timePreMessage = (timePreMessage + sfl_time) / 2


# def send_email(mail, title, text):
#     os.system(f"echo \"{text}\" | mail -s \"{title}\" {mail}")


def score_list(group):
    if str(group) not in MESSAGE_COUNTER or len(MESSAGE_COUNTER[str(group)]) == 0:
        return "1. Null\n2. Null\n3. Null"
    a = sorted(MESSAGE_COUNTER[str(group)].items(), key=lambda item: item[1], reverse=True)
    b = len(MESSAGE_COUNTER[str(group)])
    if b == 1:
        return f"1. [CQ:at,qq={a[0][0]}] - {a[0][1]}\n2. Null\n3. Null"
    elif b == 2:
        return f"1. [CQ:at,qq={a[0][0]}] - {a[0][1]}\n2. [CQ:at,qq={a[1][0]}] - {a[1][1]}\n3. Null"
    else:
        return f"1. [CQ:at,qq={a[0][0]}] - {a[0][1]}\n2. [CQ:at,qq={a[1][0]}] - {a[1][1]}\n3. [CQ:at,qq={a[2][0]}] - {a[2][1]}"


def post2http(url, server_addr=HTTPURL, data=None):
    return requests.post(f"http://{server_addr}{url}", data=data)


# 定义一个用来接收监听数据的方法
def on_message(ws, message):
    threading.Thread(target=temps_message, args=(ws, message)).start()


# 定义一个用来处理错误的方法
def on_error(_, error):
    logging.warning("-----连接出现异常,异常信息如下-----")
    logging.warning(error)


# 定义一个用来处理关闭连接的方法
def on_close(_, a, b):
    logging.error("-------连接已关闭------")
    stop()


def goodmor(target=None):
    response = requests.request("POST", "https://v2.alapi.cn/api/zaobao", data="token=CPmfvyrbNdiUBIwI&format=image",
                                headers={'Content-Type': "application/x-www-form-urlencoded"})

    msg1 = "早上好呀~ [CQ:image,file=base64://{}]".format(base64.b64encode(response.content).decode())
    # requests.post(url="http://localhost:25666/url2base64", data={"url": "https://news.topurl.cn/"}).text.replace(
    #     "\n", "")

    s = getGroups()
    if target:
        sendMessage(msg1, target_group=target)
    else:
        for i in s:
            sendMessage(msg1, target_group=i)
            time.sleep(random.randint(1500, 2000) / 1000)


def msg_counter_send(target=None):
    global MESSAGE_COUNTER
    s = getGroups()
    if target:
        msg1 = "一天结束了呢 这是今日的活跃榜 ^_^\n\n" + score_list(target)
        sendMessage(msg1, target_group=target)
    else:
        for i in s:
            msg1 = "一天结束了呢 这是今日的活跃榜 ^_^\n\n" + score_list(i)
            sendMessage(msg1, target_group=i)
            time.sleep(random.randint(1500, 2000) / 1000)
        MESSAGE_COUNTER = {}


def watchdog():
    def infoMsg(text1):
        logging.info("[WatchDog] " + text1)
        try:
            sendMessage("[WatchDog] " + text1, target_group=1019068934)
        except:
            pass

    infoMsg("Watchdog Thread is running")
    lastLessThreadWarn = 0
    lastMoreThreadWarn = 0
    memoryWarn = 0
    cpuWarn = 0
    last_tip = time.time()

    # Start Watching
    while 1:
        try:
            time.sleep(0.01)

            # Threads Check
            rt = threading.enumerate()
            nr = [i for i in ["Scheduler", "WebSocket", "WatchDog", "MainThread"] if i not in [i.name for i in rt]]

            if len(nr) != 0:
                if (time.time() - lastLessThreadWarn) >= 10:
                    infoMsg(f"警告: 有部分关键进程没在运行!\n{nr}")
                    lastLessThreadWarn = time.time()

            if len(rt) >= 50:
                if (time.time() - lastMoreThreadWarn) >= 10:
                    infoMsg(f"警告: 运行线程过多! 当前运行线程数量:{len(rt)}")
                    lastMoreThreadWarn = time.time()

            if "MainThread" in nr:
                raise KeyboardInterrupt()

            # Server Status Check
            cpu_usage = psutil.cpu_times_percent().user + psutil.cpu_times_percent().system
            memory_usage = psutil.virtual_memory().percent

            if memory_usage >= 87 and time.time() - memoryWarn >= 10:
                infoMsg(f"警告: 运存占用过多! 当前占用:{memory_usage}%")
                memoryWarn = time.time()

            if cpu_usage >= 80 and time.time() - cpuWarn >= 10:
                infoMsg(f"警告: CPU占用过高! 当前占用:{cpu_usage}%")
                cpuWarn = time.time()

            # Running Tips
            # if time.time() % 1800 == 0.0:
            if time.time() - last_tip >= 1800:
                infoMsg(f"当前机器人运行状态:\nCPU: {cpu_usage}%\nMemory: {memory_usage}%\nRunning Threads: {len(rt)}")
                last_tip = time.time()
        except KeyboardInterrupt:
            infoMsg("Watchdog Thread is stopping")
            return
        except BaseException as e:
            infoMsg(f"警告: WatchDog线程出现错误!!\n[CQ:image,file=base64://{text2image(traceback.format_exc())}]")


def goodnig():
    msg1 = "很晚了!该睡了!"
    s = getGroups()
    for i in s:
        sendMessage(msg1, target_group=i)
        time.sleep(random.randint(700, 1100) / 1000)


def main():
    try:
        logging.info("Starting... (0/5)")
        read_config()
        logging.info("Starting... (1/5)")
        ws = websocket.WebSocketApp("ws://" + WSURL + "/all?qq=1643406018",
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close,
                                    )
        t3 = threading.Thread(target=ws.run_forever)
        t3.daemon = True
        logging.info("Starting... (2/5)")
        sched = BlockingScheduler()
        sched.add_job(goodmor, 'cron', hour=7)
        sched.add_job(goodnig, 'cron', hour=22, minute=30)
        sched.add_job(msg_counter_send, 'cron', hour=0)
        t1 = threading.Thread(target=sched.start)
        t1.deamon = True
        logging.info("Starting... (3/6)")
        t1.start()
        t1.name = "Scheduler"
        logging.info("Starting... (4/6)")
        t3.start()
        t3.name = "WebSocket"
        logging.info("Starting... (5/6)")

        t4 = threading.Thread(target=watchdog)
        t4.start()
        logging.info("Starting... (6/6)")
        logging.info("Started")
        t4.name = "WatchDog"
        t4.join()
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        stop()
    except BaseException:
        logging.error("遇到无法恢复的错误 即将退出")
        logging.error(traceback.format_exc())
        stop()


if __name__ == "__main__":
    main()
