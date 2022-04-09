import json
import logging
import random
import threading
import time

import psutil
import requests

from utils import config

if __name__ == '__main__':
    from anti_spam import strQ2B



class Group:
    def __init__(self, gid):
        self.id = int(gid)

    def get_users(self):
        return getGroupUser(self.id)

    def mute(self, user, mute_time):
        mutePerson(self.id, user.id, mute_time)

    def isverify(self):
        global VERIDIED
        if str(self.id) in VERIFIED:
            return True
        return False

    def verify_info(self):
        global VERIFIED, VERIFYING
        if str(self.id) in VERIFIED:
            return f"已验证 绑定邮箱:{VERIFIED[str(self.id)]}"
        elif str(self.id) in VERIFYING:
            return f"正在验证..."
        else:
            return f"未验证! 请使用 !mail 指令查看如何激活"


class User:
    def __init__(self, uid, nickname):
        self.id = int(uid)
        self.name = nickname

    def add2blacklist(self):
        global BLACK_LIST
        if self.id not in BLACK_LIST and self.id != 1584784496:
            BLACK_LIST.append(self.id)

    def remove4blacklist(self):
        global BLACK_LIST
        BLACK_LIST.remove(self.id)

    def isblack(self):
        global BLACK_LIST
        return self.id in BLACK_LIST

    def isadmin(self):
        global ADMIN_LIST
        return self.id in ADMIN_LIST

    def add2admin(self):
        global ADMIN_LIST
        if self.id not in ADMIN_LIST:
            ADMIN_LIST.append(self.id)

    def remove4admin(self):
        global ADMIN_LIST
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
                self.success = True
            else:
                raise Exception()

    def mute(self, _time):
        self.group.mute(self.sender, _time)

    def recall(self):
        recall(self.id)

    def fast_reply(self, message, at=True, reply=True):
        temp1 = [None, None]

        if at:
            temp1[0] = self.sender.id

        if reply:
            temp1[1] = self.id

        sendMessage(message, target_qq=temp1[0], target_group=self.group.id, message_id=temp1[1])


def mutePerson(group, qq_number, mute_time):
    global HTTPURL
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
    global HTTPURL
    data1 = {
        "message_id": int(msg_id)
    }
    requests.post(url="http://" + HTTPURL + "/delete_msg", data=data1)


def sendMessage(message, target_qq=None, target_group=None, message_id=None):
    global HTTPURL
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
    global HTTPURL
    users = []
    a = requests.get(url="http://" + HTTPURL + "/get_group_member_list?group_id={}".format(groupID))
    if a.status_code != 200:
        raise ConnectionError()
    else:
        for i in a.json()["data"]:
            users.append(i["user_id"])
        return users


def getGroups():
    global HTTPURL
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


def healthy_check():
    score = 10.0
    threads = threading.active_count()
    if threads >= 40:
        score -= 4
    else:
        score -= threads/10

    menory = psutil.Process().memory_info()


def stop():
    global ADMIN_LIST, BLACK_LIST, VERIFIED, INTRODUCE, ACCOMPLISHMENT
    logging.info("Restarting...")
    config.save_config(ADMIN_LIST, BLACK_LIST, VERIFIED, INTRODUCE, ACCOMPLISHMENT)
    psutil.Process().kill()


def get_runtime():
    global recordTime
    nowtime = int(time.time())
    return "{}秒".format(int(nowtime - recordTime))