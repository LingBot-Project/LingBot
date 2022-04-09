# -*- coding: UTF-8 -*-
import json
import logging
import os
import random
import re
import threading
import time
import traceback

import hypixel
import requests
import websocket
from apscheduler.schedulers.blocking import BlockingScheduler

import utils.qqbot
from modules import achievements, bilibili, bot_utils, imgs, introduce, math, music, one_line, play
from utils.anti_spam import spammer_checker, simhash_similarity
from utils.image import text2image
from utils.qqbot import sendMessage, getGroups, Group, Message, stop

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S %p")

SERVER_ADDR = "127.0.0.1"
ADMIN_LIST = [1790194105, 1584784496, 2734583, 2908331301, 3040438566, 1474002938]
HYPBAN_COOKIE = None
SEND_AD_LIST = {}
BLACK_LIST = []
INTRODUCE = {"qq": {}, "waiting": []}
CACHE_MESSAGE = []
BANCHECK_UID = {}
WSURL = SERVER_ADDR + ":10540"
HTTPURL = SERVER_ADDR + ":10500"
ALL_MESSAGE = 0
MESSAGE_PRE_MINUTE = [0, 0]
ALL_AD = 0
timePreMessage = 0
recordTime = int(time.time())
isChatBypassOpened = False
ANTISPAMMER = {}
IGNORE_GROUP = [1079822858]
FEEDBACKS = {}
REPEATER = []
SPAM2_MSG = {}
SPAM2_VL = {}
EMAIL_DELAY = {}
VERIFIED = {}
VERIFYING = {}
VERIFY_TIPS = {}

# URL_LIST = r'.*.net|.*.com|.*.xyz|.*.me|.*.'
ANTI_AD = r"送福利|定制水影|加群.*[0-9]{5,10}|.*内部|\n元|破甲|天花板|工具箱|绕更新|开端|不封号|外部|.* toolbox|替换au|绕过(盒子)vape检测|内部|防封|封号|waibu|外部|.*公益|晋商|禁商|盒子更新后|小号机|群.*[0-9]{5,10}|\d{2,4}红利项目|躺赚|咨询(\+)|捡钱(模式)|(个人)创业|带价私聊|出.*号|裙.*[0-9]{5,10}|君羊.*[0-9]{5,10}|q(\:)[0-9]{5,10}|免费(获取)|.*launcher|3xl?top|.*小卖铺|cpd(d)|暴打|对刀|不服|稳定奔放|qq[0-9]{5,10}|定制.*|小卖铺|老婆不在家(刺激)|代购.*|vape"

spam2_vl_reset_cool_down = time.time()


def on_message2(ws, message):
    global HYPBAN_COOKIE, isChatBypassOpened, \
        CACHE_MESSAGE, timePreMessage, \
        MESSAGE_PRE_MINUTE, ALL_MESSAGE, \
        ALL_AD, FEEDBACKS, \
        spam2_vl_reset_cool_down, VERIFYING, VERIFIED, VERIFY_TIPS

    a = json.loads(message)
    logging.debug(a)
    if a["post_type"] == "notice" and a["notice_type"] == "notify" and a["sub_type"] == "poke" and "group_id" in a and \
            a["target_id"] == a["self_id"] and Group(a["group_id"]).isverify():
        sendMessage(random.choice(
            ["不要戳我啦 =w=", "不要动我!", "唔...", "Hentai!", "再戳...会...会变奇怪的..", "啊啊啊不要再戳我辣!!!", "好痛! 呜~", "Nya~"]),
            target_group=a["group_id"], target_qq=a["user_id"])
        sendMessage(f"[CQ:poke,qq={a['user_id']}]", target_group=a["group_id"])
        return

    msg = Message(message)

    try:
        # 处理消息内容
        def del_this(list):
            if list == "this":
                return msg.group.id
            else:
                return list

        if msg.text == "":
            return

        if msg.id in CACHE_MESSAGE:
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

        command_list = msg.text.split(" ")

        logging.info("[{0}] {1}({2}) {3}".format(msg.group.id, msg.sender.name, msg.sender.id, msg.text))

        if msg.text in ["!help", "菜单"]:
            msg.fast_reply(f"请访问: https://lingbot.guimc.ltd/\nLingbot官方群：308089090\n本群验证状态:{msg.group.verify_info()}")

        if command_list[0] == "!mail":
            msg.group.id = str(msg.group.id)
            if len(command_list) == 1:
                msg.fast_reply("""邮箱验证指令:
开始验证: !mail verify 邮箱地址
完成验证: !mail code 验证码
查看本群验证状态: !help""")
                return
            if command_list[1] == "verify":
                if msg.group.id in VERIFIED:
                    msg.fast_reply("本群已经验证过了! 输入 !help 可以查询激活状态")
                    return

                if msg.group.id not in VERIFYING:
                    VERIFYING[msg.group.id] = {
                        "time": 0,
                        "code": "",
                        "user": 0,
                        "mail": ""
                    }

                if time.time() - float(VERIFYING[msg.group.id]["time"]) < 300:
                    msg.fast_reply(
                        "已经有人发起了一个验证消息了! 请等待: {}s".format(300 - (time.time() - float(VERIFYING[msg.group.id]["time"]))))
                    return

                print(a["sender"]["role"])

                if a["sender"]["role"] == "member" and not msg.sender.isadmin():
                    msg.fast_reply("目前不支持普通群成员发起验证!")
                    return

                VERIFYING[msg.group.id]["mail"] = command_list[2]
                VERIFYING[msg.group.id]["user"] = msg.sender.id
                VERIFYING[msg.group.id]["code"] = str(random.randint(100000000, 999999999))
                VERIFYING[msg.group.id]["time"] = time.time()
                send_email(command_list[2], f"[LingBot Team] 群{msg.group.id} - 激活", f"""您好, {msg.sender.name}:
感谢您使用 LingBot 机器人, 您正在尝试给群 {msg.group.id} 激活! 您的验证码是: {VERIFYING[msg.group.id]["code"]}
请您在群内使用指令 !mail code {VERIFYING[msg.group.id]["code"]} 来激活!
此验证码 30 分钟内有效.""")
                msg.fast_reply("我们已经尝试发送一封电子邮件到您的邮箱 请按照邮箱内容操作")
                return

            if command_list[1] == "code":
                if msg.group.id not in VERIFYING:
                    msg.fast_reply("没有查到本群的激活信息!")
                    return

                if time.time() - VERIFYING[msg.group.id]["time"] >= 1800:
                    msg.fast_reply("""本群的验证码已经过期了!
邮箱验证指令:
开始验证: !mail verify 邮箱地址
完成验证: !mail code 验证码
查看本群验证状态: !help""")
                    return

                if str(command_list[2]) == VERIFYING[msg.group.id]["code"]:
                    msg.fast_reply("激活成功!")
                    VERIFIED[msg.group.id] = VERIFYING[msg.group.id]["mail"]

        if msg.text in ["!restart", "!quit"] and msg.sender.isadmin():
            msg.fast_reply("Restarting...")
            print(requests.get("http://" + HTTPURL + "/set_restart").text)
            stop()

        if not msg.group.isverify():
            try:
                if str(msg.group.id) not in VERIFY_TIPS:
                    VERIFY_TIPS[str(msg.group.id)] = 0
                if time.time() - VERIFY_TIPS[str(msg.group.id)] <= 120:
                    msg.fast_reply("本群还没有激活! 请及时联系管理员激活!! 激活方式 !mail verify 邮箱地址\n注意 禁言机器人会进入黑名单!", reply=False,
                                   at=False)
                    VERIFY_TIPS[str(msg.group.id)] = time.time()
            except:
                pass
            finally:
                return

        if msg.sender.id not in SPAM2_MSG:
            SPAM2_MSG[msg.sender.id] = msg.text
            SPAM2_VL[msg.sender.id] = 0
        _simhash_dis = simhash_similarity(str(SPAM2_MSG[msg.sender.id]).lower(), msg.text.lower())
        if _simhash_dis >= 0.836:
            SPAM2_VL[msg.sender.id] += 10
            if _simhash_dis >= 0.99:
                SPAM2_VL[msg.sender.id] += 10

            if SPAM2_VL[msg.sender.id] >= 55:
                # if msg.sender.isadmin():
                #     sendMessage(
                #         f"{msg.sender.id}发送的一条消息疑似重复, 且此人在超管名单内\n上一条内容: \n {SPAM2_MSG[msg.sender.id]}\n内容:\n{msg.text}\n相似度: {_simhash_dis}\nVL: {SPAM2_VL[msg.sender.id]}",
                #         target_group=1019068934)
                # msg.recall()
                if SPAM2_VL[msg.sender.id] >= 200:
                    msg.mute(43199 * 60)  # :259200
                    SPAM2_VL[msg.sender.id] -= 20
                    return
                # else:
                #     msg.mute(600)
                # msg.fast_reply("您貌似在刷屏/群发?", reply=False)
                # return
            SPAM2_MSG[msg.sender.id] = msg.text
        else:
            SPAM2_MSG[msg.sender.id] = msg.text
            if SPAM2_VL[msg.sender.id] > 0:
                SPAM2_VL[msg.sender.id] -= 2

        reScan = re.findall(
            ANTI_AD,
            msg.text.replace(" ", "").replace(".", "").replace("\n", "").lower())
        if len(msg.text) >= 33 and len(reScan) >= 2:
            SPAM2_VL[msg.sender.id] += 4
            if msg.sender.isadmin():
                sendMessage("{}发送的一条消息触发了正则 并且此人在超管名单内\n内容:\n{}".format(msg.sender.id, msg.text),
                            target_group=1019068934)
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
            msg.fast_reply("您的名称中似乎存在广告", reply=False)
            ALL_AD += 1
            return

        if len(msg.text) > 1500:
            msg.mute(600)
            msg.recall()
            msg.fast_reply("消息太长了哟", reply=False)
            SPAM2_VL[msg.sender.id] += 3
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
                msg.fast_reply("您发送的合并转发内容貌似有广告!", reply=False)
                msg.mute(3600)
                msg.recall()
                ALL_AD += 1
                SPAM2_VL[msg.sender.id] += 3
                return

        try:
            if spammer_checker(msg):
                msg.mute(60)
                msg.recall()
                msg.fast_reply("您的说话速度有点快，是不是在刷屏呢？", reply=False)
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
                msg.fast_reply("太...太多图片了..", reply=False)
                return

        if (msg.group.id, msg.sender.id) in REPEATER:
            if not (command_list[0] == "!repeater" and (command_list[1] == "add" or command_list[1] == "remove")):
                msg.fast_reply(msg.text, reply=False, at=False)

        if command_list[0] == "!msg_test":
            msg.fast_reply(f"""{''.join(json.dumps(command_list))}
{msg.text}""")

        achievements.on_message(msg, command_list)
        bilibili.on_message(msg, command_list)
        bot_utils.on_message(msg, command_list)
        hypixel.on_message(msg, command_list)
        imgs.on_message(msg, command_list)
        introduce.on_message(msg, command_list)
        math.on_message(msg, command_list)
        music.on_message(msg, command_list)
        one_line.on_message(msg, command_list)
        play.on_message(msg, command_list)

    except Exception as e:
        a = traceback.format_exc()
        logging.error(a)
        msg.fast_reply(
            "很抱歉，我们在执行你的指令时出现了一个问题 =_=\n各指令用法请查看 https://lingbot.guimc.ltd/\n[CQ:image,file=base64://{}]".format(
                text2image(a)))


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


def send_email(mail, title, text):
    os.system(f"echo \"{text}\" | mail -s \"{title}\" {mail}")


# 定义一个用来接收监听数据的方法
def on_message(ws, message):
    threading.Thread(target=temps_message, args=(ws, message)).start()


# 定义一个用来处理错误的方法
def on_error(ws, error):
    logging.warning("-----连接出现异常,异常信息如下-----")
    logging.warning(error)


# 定义一个用来处理关闭连接的方法
def on_close(ws, a, b):
    logging.error("-------连接已关闭------")
    stop()


def goodmor(target=None):
    msg1 = "早上好呀~ [CQ:image,file=base64://{}]".format(
        requests.post(url="http://localhost:25666/url2base64", data={"url": "https://news.topurl.cn/"}).text.replace(
            "\n", ""))
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
    global ADMIN_LIST, BLACK_LIST, VERIFIED, INTRODUCE
    try:
        logging.info("Starting... (0/5)")
        ADMIN_LIST, BLACK_LIST, VERIFIED, INTRODUCE, achievements.ACCOMPLISHMENT = utils.qqbot.read_config()
        logging.info("Starting... (1/5)")
        ws = websocket.WebSocketApp("ws://" + WSURL + "/all?verifyKey=uThZyFeQwJbD&qq=3026726134",
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
        t1 = threading.Thread(target=sched.start)
        t1.deamon = True
        logging.info("Starting... (3/5)")
        t1.start()
        logging.info("Starting... (4/5)")
        t3.start()
        logging.info("Starting... (5/5)")
        sendMessage("restart successful", target_group=1019068934)
        logging.info("Bot Ready!")
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
