import json
import random
import re

import requests

from utils.User import User
from utils.Group import Group

# from main import HTTPURL, strQ2B, Group, User

DEV_GROUP = 1019068934


# 先分类吧
class Message:
    def __init__(self, json2msg=None):
        self.id = 0
        self.text = ""
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


def sendMessage(message, target_qq=None, target_group=None, message_id=None, bypass=False, bypass_length=4):
    if target_qq is None and target_group is None:
        raise Exception()

    message = str(message)
    if target_group is not None:
        # 消息前缀 通常用于 At 回复消息
        prefix = ""

        if target_qq is not None:
            prefix += "[CQ:at,qq={}]".format(target_qq)

        if message_id is not None:
            prefix += "[CQ:reply,id={}]".format(message_id)

        if bypass:
            b_array = ["\u202D"]  # ["\u202D", "", "", "", ""]
            for i in range(0, bypass_length):
                b_array.append("")
            nowmsg = ""
            for i2 in list(message):
                nowmsg += i2 + random.choice(b_array)
            message = nowmsg
        
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
        ...
        # logging.warning("目前暂时不支持发送私聊消息")


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


def post2http(url, server_addr='127.0.0.1:10500', data=None):
    return requests.post(f"http://{server_addr}{url}", data=data)

