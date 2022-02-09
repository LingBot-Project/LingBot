# -*- coding: UTF-8 -*-
import base64
import json
import os
import random
import re
import sys
import threading
import time
import traceback
from io import BytesIO

import client
import requests
import websocket
from mcstatus import MinecraftServer
from PIL import Image, ImageDraw, ImageFont

SERVER_ADDR = "127.0.0.1"
ADMIN_LIST = [1790194105, 1584784496, 2734583, 2908331301, 3040438566]
HYPBAN_COOKIE = None
SEND_AD_LIST = {}
BLACK_LIST = []
CACHE_MESSAGE = []
BANCHECK_UID = {}
WSURL = SERVER_ADDR+":10540"
HTTPURL = SERVER_ADDR+":10500"
MC_MOTD_COLORFUL = re.compile(r"§.")
ALLOWRUNNING = True
NICKNAME_LOCKED = []
isChatBypassOpened = False
unicodeSymbolList = ["‍", "‌", "‭"]


def readConfig():
    global ADMIN_LIST, BLACK_LIST
    if os.path.isfile('config.json') == False:
        f = open('config.json', 'w')
        f.write("")
        f.close()
    f = open('config.json', 'r')
    s = json.loads(f.read())
    try:
        ADMIN_LIST = s["admin"]
    except:
        pass
    try:
        BLACK_LIST = s["blacklist"]
    except:
        pass
    try:
        NICKNAME_LOCKED = s["nickname_locked"]
    except:
        pass
    f.close()



def saveConfig():
    global ADMIN_LIST, BLACK_LIST
    f = open('config.json', 'w')
    s = {
        "admin": ADMIN_LIST,
        "blacklist": BLACK_LIST
    }
    f.write(json.dumps(s))
    f.close()


def quit():
    print("Try to Quit...")
    saveConfig()
    sys.exit(0)


def text2image(text):
    imageuid = str(random.randint(10000000,9999999999))
    fontSize = 22
    max_w = 0
    lines = text.split('\n')
    # print(len(lines))
    fontPath = r"a.ttf"
    font = ImageFont.truetype(fontPath, fontSize)
    for i in lines:
        if max_w <= font.getmask(i).getbbox()[2]:
            max_w = font.getmask(i).getbbox()[2]
    im = Image.new("RGB", (max_w+11, len(lines)*(fontSize+8)), (255, 255, 255))
    dr = ImageDraw.Draw(im)
    dr.text((1, 1), text, font=font, fill="#000000")
    im.save(imageuid+".cache.png")
    with open(imageuid+".cache.png", "rb") as f:
        return base64.b64encode(f.read()).decode()


def strQ2B(ustring):
    rstring = ""
    for uchar in ustring:
        inside_code = ord(uchar)
        if inside_code == 12288:
            inside_code = 32
        elif inside_code >= 65281 and inside_code <= 65374:
            inside_code -= 65248

        rstring += chr(inside_code)
    return rstring
    
    
def on_guild_message(ad):
    global HYPBAN_COOKIE, isChatBypassOpened, CACHE_MESSAGE
    guild_id = ad["guild_id"]
    channel_id = ad["channel_id"]
    message_id = ad["message_id"]
    message_text = ad["message"]
    sender_id = ad["sender"]["user_id"]
    sender_name = ad["sender"]["nickname"]
    if message_text == "":
        return
    command_list = message_text.split(" ")
    if message_text == "#test":
        sendGuildmsg(guild_id, channel_id, message_id, sender_id, "Hello!")
            
    if command_list[0] == "#help":
        sendGuildmsg(guild_id, channel_id, message_id, sender_id, "请访问: https://lingbot.guimc.ltd/")
    
    if message_text == "一语":
        sendGuildmsg(guild_id, channel_id, message_id, sender_id, requests.get("http://api.muxiuge.cn/API/society.php").json()["text"])
    if command_list[0] in ["#hypban", "!hypban", "#hyp", "#ban"]:
        try:
            if len(command_list)<=2:
                sendGuildmsg(guild_id, channel_id, message_id, sender_id, "正确格式:#hypban <USERNAME> <BANID>")
            else:
                if sender_id not in BANCHECK_UID:
                    BANCHECK_UID[sender_id] = time.time()
                elif time.time() - BANCHECK_UID[sender_id] <= 60:
                    sendGuildmsg(guild_id, channel_id, message_id, sender_id, "进入冷却时间 可在{}秒后使用".format(round(60.0 - (time.time() - BANCHECK_UID[sender_id]), 2)))
                    return
                sendGuildmsg(guild_id, channel_id, message_id, sender_id, "请稍等 正在向远程服务器发送请求")
                userName = command_list[1]
                BanID = command_list[2].replace("#", "")
                # mutePerson(group_number,sender_qqnumber,5)
                if userName.find("$") != -1 & userName.find("{") != -1:
                    sendGuildmsg(guild_id, channel_id, message_id, sender_id, "Firewall defense")
                    back=False
                else:
                    if BanID.find("$") != -1 & BanID.find("{") != -1:
                        sendGuildmsg(guild_id, channel_id, message_id, sender_id, "Firewall defense")
                        back=False
                    else:
                        a = ""
                        c = 1
                        while True:
                            print("Username:{} BanID:{}".format(userName, BanID))
                            a = client.ban(userName, BanID)
                            if a.find("too many request") == -1:
                                break
                            else:
                                # sendGroupmsg(group_number,message_id,sender_qqnumber,a)
                                if c == 1:
                                    sendGuildmsg(guild_id, channel_id, message_id, sender_id, "请稍等 我们正在自动重新请求 将在请求成功后返回")
                                    c = 0
                            time.sleep(3)
                        print(a)
                        # a+="查ban冷却5秒"
                        # 没有意义 :(((
                        if a.find("ERR|") != -1:
                            sendGuildmsg(guild_id, channel_id, message_id, sender_id, a)
                        else:
                            BANCHECK_UID[sender_id] = time.time()
                            sendGuildmsg(guild_id, channel_id, message_id, sender_id, "[CQ:image,file=base64://"+text2image(a)+"]")
        except:
            sendGuildmsg(guild_id, channel_id, message_id, sender_id, "由于不明原因 执行失败")
            print(traceback.format_exc())
    if message_text == "一话":
        sendGuildmsg(guild_id, channel_id, message_id, sender_id, "[CQ:image,file=base64://"+text2image(
                     requests.get("http://api.muxiuge.cn/API/society.php").json()["text"])+"]")
        sendGuildmsg(guild_id, channel_id, message_id, sender_id, "[CQ:image,file=base64://"+text2image(
                     requests.get("http://open.iciba.com/dsapi/").json()["content"] + "\n" +
                     requests.get("http://open.iciba.com/dsapi/").json()["note"])+"]")
    if message_text == "一英":
        sendGuildmsg(guild_id, channel_id, message_id, sender_id, "[CQ:image,file=base64://"+text2image(
                     requests.get("http://open.iciba.com/dsapi/").json()["content"] + "\n" +
                     requests.get("http://open.iciba.com/dsapi/").json()["note"])+"]")
    if command_list[0] == "/mcping":
        try:
            server = MinecraftServer.lookup(command_list[1]).status()
            aaa = "Motd:\n{0}\n在线人数:{1}/{2}\nPing:{3}\nVersion:{4} (protocol:{5})".format(
            re.sub(MC_MOTD_COLORFUL, "", server.description), server.players.online, server.players.max,
            server.latency, re.sub(MC_MOTD_COLORFUL, "", server.version.name), server.version.protocol)
            aaa = aaa.replace("Hypixel Network", "嘉心糖 Network")
            aaa = "[CQ:image,file=base64://{}]".format(text2image(aaa))
            if server.favicon is not None:
                aaa = aaa + "\n[CQ:image,file="+server.favicon.replace("data:image/png;base64,", "base64://")+"]"
            sendGuildmsg(guild_id, channel_id, message_id, sender_id, aaa)
        except Exception as e:
            sendGuildmsg(guild_id, channel_id, message_id, sender_id, "[CQ:image,file=base64://"+text2image("由于不明原因 执行失败")+"]")
            print(traceback.format_exc())
    if command_list[0] == "#fdpinfo":
        # https://bstats.org/api/v1/plugins/11076/charts/<Type>/data
        try:
            if command_list[1] == "online":
                url = "https://bstats.org/api/v1/plugins/11076/charts/minecraftVersion/data"
                a = requests.get(url=url).json()
                onlinePlayer = 0
                for i in a:
                    onlinePlayer += i["y"]
                sendGuildmsg(guild_id, channel_id, message_id, sender_id, "[CQ:image,file=base64://"+text2image("OnlinePlayers: {}".format(onlinePlayer))+"]")
            elif command_list[1] == "versions":
                url = "https://bstats.org/api/v1/plugins/11076/charts/pluginVersion/data"
                a = requests.get(url=url).json()
                onlineVersion = []
                for i in a:
                    onlineVersion.append("{}: {}".format(i["name"], i["y"]))
                sendGuildmsg(guild_id, channel_id, message_id, sender_id,
                             "[CQ:image,file=base64://"+text2image("OnlineVersionsInfo:\n{}".format("\n".join(onlineVersion)))+"]")
            elif command_list[1] == "systems":
                url = "https://bstats.org/api/v1/plugins/11076/charts/os/data"
                a = requests.get(url=url).json()
                onlineSystem = []
                for i in a["seriesData"]:
                    onlineSystem.append("{}: {}".format(i["name"], i["y"]))
                sendGuildmsg(guild_id, channel_id, message_id, sender_id,
                             "[CQ:image,file=base64://"+text2image("OnlineSystms:\n{}".format("\n".join(onlineSystem)))+"]")
            elif command_list[1] == "countries":
                url = "https://bstats.org/api/v1/plugins/11076/charts/location/data"
                a = requests.get(url=url).json()
                onlineCountry = []
                for i in a:
                    onlineCountry.append("{}: {}".format(i["name"], i["y"]))
                sendGuildmsg(guild_id, channel_id, message_id, sender_id,
                             "[CQ:image,file=base64://"+text2image("OnlineCountrys:\n{}".format("\n".join(onlineCountry)))+"]")
            elif command_list[1] == "beta":
                sendGuildmsg(guild_id, channel_id, message_id, sender_id, "Please wait...")
                url = "https://api.github.com/repos/UnlegitMC/FDPClient/actions/runs"
                a = requests.get(url=url).json()
                objectIDs = []
                for i in a["workflow_runs"]:
                    if i["name"] == "build":
                        objectIDs.append(i["id"])
                actionInfo = requests.get(url="https://api.github.com/repos/UnlegitMC/FDPClient/actions/runs/{}".format(objectIDs[0])).json()
                updTime = actionInfo["head_commit"]["timestamp"]
                updMsg = actionInfo["head_commit"]["message"]
                updAuthor = "{} ({})".format(actionInfo["head_commit"]["author"]["name"], actionInfo["head_commit"]["author"]["email"])
                sendGuildmsg(guild_id, channel_id, message_id, sender_id,
                             "Update Time:{}\n"
                             "Update Message:{}\n"
                             "Author:{}\n"
                             "Download URL:https://nightly.link/UnlegitMC/FDPClient/actions/runs/{}/FDPClient.zip\n".format(updTime, updMsg, updAuthor, objectIDs[0]))
            elif command_list[1] == "release":
                url = "https://api.github.com/repos/UnlegitMC/FDPClient/releases/latest"
                a = requests.get(url=url).json()
                files = []
                for i in a["assets"]:
                    files.append("{}: {}".format(i["name"], i["browser_download_url"].replace("github.com", "hub.fastgit.org")))
                sendGuildmsg(guild_id, channel_id, message_id, sender_id,
                             "Version: {}\n".format(a["name"])+"\n".join(files))
        except Exception as e:
            sendGuildmsg(guild_id, channel_id, message_id, sender_id, "由于不明原因 执行失败")
            print(traceback.format_exc())


def on_message2(ws, message):
    global HYPBAN_COOKIE, isChatBypassOpened, CACHE_MESSAGE
    try:
        a = json.loads(message)
        message_text = ""
        message_id = 0
        ad = a
        if ad["post_type"] == "message":
            if ad["message_type"] == "guild":
                on_guild_message(ad)
                return
            elif ad["message_type"] != "group":
                return
        else:
            return
        message_text = ad["message"]
        message_text = strQ2B(message_text)
        for i in unicodeSymbolList:
            message_text.replace(i, "")
        sender_qqnumber = ad["sender"]["user_id"]
        sender_name = ad["sender"]["nickname"]
        group_number = ad["group_id"]
        message_id = ad["message_id"]
        if message_text == "":
            return
        reScan = re.search(
            "加群(:)[0-9]{5,10}|.*内部|\\n元|破甲|天花板|工具箱|绕更新|开端|不封号|外部|.* toolbox|替换au|绕过(盒子)vape检测|外部|防封|封号|waibu|晋商|禁商|盒子更新后|跑路|小号机|群(号)(:)[0-9]{5,10}|\d{2,4}红利项目|躺赚|咨询(\+)|捡钱(模式)|(个人)创业|交流群|带价私聊|出.*号|裙(号)(:)[0-9]{5,10}|群(号)(:)[0-9]{5,10}|Q[0-9]{5,10}|免费(获取)|.*(L|l)auncher|.*(公益)配置",
            message_text.replace(" ", "").replace(".", "").replace("\n", ""))
        if len(message_text) > 35 and reScan != None:
            if sender_qqnumber in ADMIN_LIST:
                return
            time.sleep(1)
            mutePerson(group_number, sender_qqnumber, 600)
            recall(message_id)
        
        print("[{0}] {1}({2}) {3}".format(group_number, sender_name, sender_qqnumber, message_text))

        if sender_qqnumber in BLACK_LIST:
            recall(message_id)
            return

        command_list = message_text.split(" ")
        if message_text == "#test":
            sendGroupmsg(group_number, message_id, sender_qqnumber, "Hello!")
            
        if command_list[0] == "#help":
            sendGroupmsg(group_number, message_id, sender_qqnumber, "请访问: https://newbotdoc.guimc.ltd/")

        if message_text == "一语":
            sendGroupmsg(group_number, message_id, sender_qqnumber,
                         requests.get("http://api.muxiuge.cn/API/society.php").json()["text"])
        
        if message_text.find("[CQ:json,data=") != -1:
            message_text = message_text.replace("\\/", "/")
            if message_text.find('"jumpUrl":"https://b23.tv/') != -1:
                str1 = requests.get(url="https://api.bilibili.com/x/web-interface/view?bvid={}".format(re.findall(r'<link data-vue-meta="true" rel="canonical" href="https://www.bilibili.com/video/.*/">',requests.get(json.loads(re.findall(r"\[CQ:json,data=.*\]",message_text)[0].replace("[CQ:json,data=","").replace("&#44;",",")[:-1])["meta"]["news"]["jumpUrl"].replace("&amp;", "&")).text)[0].replace(r'<link data-vue-meta="true" rel="canonical" href="https://www.bilibili.com/video/', "")[:-3])).json()
                if str1["code"] != 0:
                    print("查询失败")
                    sys.exit(1)
                str1 = str1["data"]
                response = requests.get(str1["pic"])
                im_vl = Image.open(BytesIO(response.content))
                im_v = im_vl.resize((430, 270), Image.ANTIALIAS)
                imageuid = str(random.randint(10000000,9999999999))
                fontSize = 22
                max_w = 0
                s = ""
                if str1["copyright"] == 1:
                    s = "自制"
                elif str1["copyright"] == 2:
                    s = "转载"
                else:
                    s = "未曾设想的投稿类型: {}  (不是转载也不是自制?)".format(str1["copyright"])
                text = """标题: {}
    UP主: {} ({})
    投稿分区: {} ({})
    投稿类型: {}
    视频链接: https://www.bilibili.com/video/{}/
    播放量: {}
    简介:
    {}""".format(str1["title"], str1["owner"]["name"], str1["owner"]["mid"],
            str1["tname"], str1["tid"], s, str1["bvid"], str1["stat"]["view"], str1["desc"])
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
                im = Image.new("RGB", (max_w+11, (len(lines)*(fontSize+8))+280), (255, 255, 255))
                im.paste(im_v, (0,0))
                dr = ImageDraw.Draw(im)
                dr.text((1, 280), text, font=font, fill="#000000")
                im.save(imageuid+"_cache.png")
                with open(imageuid+".png", "rb") as f:
                    sendGroupmsg(group_number, message_id, sender_qqnumber, "[CQ:image,file=base64://"+base64.b64encode(f.read()).decode()+"]")
        
        if message_text == "一英":
            sendGroupmsg(group_number, message_id, sender_qqnumber,
                         requests.get("http://open.iciba.com/dsapi/").json()["content"] + "\n" +
                         requests.get("http://open.iciba.com/dsapi/").json()["note"])

        if message_text == "二次元":
            sendGroupmsgImg(group_number, message_id, sender_qqnumber,
                            base64.b64encode(requests.get("http://www.xgstudio.xyz/api").content).decode())

        if message_text == "必应壁纸":
            sendGroupmsgImg(group_number, message_id, sender_qqnumber,
                            base64.b64encode(requests.get("http://www.xgstudio.xyz/api/bing.php").content).decode())

        if message_text == "一话":
            sendGroupmsg(group_number, message_id, sender_qqnumber,
                         requests.get("http://api.muxiuge.cn/API/society.php").json()["text"])
            sendGroupmsg(group_number, message_id, sender_qqnumber,
                         requests.get("http://open.iciba.com/dsapi/").json()["content"] + "\n" +
                         requests.get("http://open.iciba.com/dsapi/").json()["note"])
        
        if command_list[0] == "#admin":
            if command_list[1] == "list":
                sendGroupmsg5(group_number, message_id, sender_qqnumber, "{}".format(ADMIN_LIST))
            if sender_qqnumber not in ADMIN_LIST:
                sendGroupmsg5(group_number, message_id, sender_qqnumber, "你的权限不足!")
                return
            if command_list[1] == "add":
                if int(command_list[2]) in ADMIN_LIST:
                    sendGroupmsg5(group_number, message_id, sender_qqnumber, "超管内已经有这个人了")
                    return
                ADMIN_LIST.append(int(command_list[2]))
                sendGroupmsg5(group_number, message_id, sender_qqnumber, "操作成功")
            elif command_list[1] == "remove":
                if int(command_list[2]) not in ADMIN_LIST:
                    sendGroupmsg5(group_number, message_id, sender_qqnumber, "超管内没有这个人")
                    return
                elif int(command_list[2]) == 1584784496:
                    sendGroupmsg5(group_number, message_id, sender_qqnumber, "由于您进行的操作过于敏感 已被拦截 并发送给Owner")
                    sendGroupmsg2(868218262, "{}尝试把您(Owner)从超管列表删除".format(sender_qqnumber))
                    return
                ADMIN_LIST.remove(int(command_list[2]))
                sendGroupmsg5(group_number, message_id, sender_qqnumber, "操作成功")
        
        if command_list[0] == "#blacklist":
            if command_list[1] == "list":
                sendGroupmsg5(group_number, message_id, sender_qqnumber, "{}".format(BLACK_LIST))
            if sender_qqnumber not in ADMIN_LIST:
                sendGroupmsg5(group_number, message_id, sender_qqnumber, "你的权限不足!")
                return
            if command_list[1] == "add":
                if int(command_list[2]) in BLACK_LIST:
                    sendGroupmsg5(group_number, message_id, sender_qqnumber, "黑名单内已经有这个人了")
                    return
                elif int(command_list[2]) == 1584784496:
                    sendGroupmsg5(group_number, message_id, sender_qqnumber, "由于您进行的操作过于敏感 已被拦截 并发送给Owner")
                    sendGroupmsg2(868218262, "{}尝试把您(Owner)添加进黑名单".format(sender_qqnumber))
                    return
                BLACK_LIST.append(int(command_list[2]))
                sendGroupmsg5(group_number, message_id, sender_qqnumber, "操作成功")
            elif command_list[1] == "remove":
                if int(command_list[2]) not in BLACK_LIST:
                    sendGroupmsg5(group_number, message_id, sender_qqnumber, "黑名单内没有这个人")
                    return
                BLACK_LIST.remove(int(command_list[2]))
                sendGroupmsg5(group_number, message_id, sender_qqnumber, "操作成功")


        if command_list[0] == "/mcping":
            try:
                server = MinecraftServer.lookup(command_list[1]).status()
                aaa = "Motd:\n{0}\n在线人数:{1}/{2}\nPing:{3}\nVersion:{4} (protocol:{5})".format(
                    re.sub(MC_MOTD_COLORFUL, "", server.description), server.players.online, server.players.max,
                    server.latency, re.sub(MC_MOTD_COLORFUL, "", server.version.name), server.version.protocol)
                aaa = aaa.replace("Hypixel Network", "嘉心糖 Network")
                aaa = "[CQ:image,file=base64://{}]".format(text2image(aaa))
                if server.favicon is not None:
                    aaa = aaa + "\n[CQ:image,file="+server.favicon.replace("data:image/png;base64,", "base64://")+"]"
                sendGroupmsg(group_number, message_id, sender_qqnumber, aaa)
            except Exception as e:
                getError(group_number, message_id, sender_qqnumber, traceback.format_exc())
                
        if command_list[0] in ["#hypban", "!hypban", "#hyp", "#ban"]:
            try:
                if len(command_list)<=2:
                    sendGroupmsg(group_number,message_id,sender_qqnumber,"正确格式:#hypban <USERNAME> <BANID>")
                else:
                    if sender_qqnumber not in BANCHECK_UID or sender_qqnumber in ADMIN_LIST:
                        BANCHECK_UID[sender_qqnumber] = time.time()
                    elif time.time() - BANCHECK_UID[sender_qqnumber] <= 60:
                        sendGroupmsg(group_number,message_id,sender_qqnumber,"进入冷却时间 可在{}秒后使用".format(round(60.0 - (time.time() - BANCHECK_UID[sender_qqnumber]), 2)))
                        return
                    sendGroupmsg(group_number,message_id,sender_qqnumber,"请稍等 正在向远程服务器发送请求")
                    userName = command_list[1]
                    BanID = command_list[2].replace("#", "")
                    # mutePerson(group_number,sender_qqnumber,5)
                    if userName.find("$") != -1 & userName.find("{") != -1:
                        sendGroupmsg(group_number,message_id,sender_qqnumber,"Firewall defense")
                        back=False
                    else:
                        if BanID.find("$") != -1 & BanID.find("{") != -1:
                            sendGroupmsg(group_number,message_id,sender_qqnumber,"Firewall defense")
                            back=False
                        else:
                            a = ""
                            c = 1
                            while True:
                                print("Username:{} BanID:{}".format(userName, BanID))
                                a = client.ban(userName, BanID)
                                if a.find("too many request") == -1:
                                    break
                                else:
                                    # sendGroupmsg(group_number,message_id,sender_qqnumber,a)
                                    if c == 1:
                                        sendGroupmsg(group_number, message_id, sender_qqnumber, "请稍等 我们正在自动重新请求 将在请求成功后返回")
                                        c = 0
                                time.sleep(3)
                            print(a)
                            # a+="查ban冷却5秒"
                            # 没有意义 :(((
                            if a.find("ERR|") != -1:
                                sendGroupmsg5(group_number, message_id, sender_qqnumber, a)
                            else:
                                BANCHECK_UID[sender_qqnumber] = time.time()
                                sendGroupmsg(group_number, message_id, sender_qqnumber, "[CQ:image,file=base64://"+text2image(a)+"]")
            except Exception as e:
                getError(group_number, message_id, sender_qqnumber, traceback.format_exc())

        if command_list[0] == "#send":
            if sender_qqnumber in ADMIN_LIST:
                if command_list[1] == "all":
                    s = getGroups()
                    sendGroupmsg(group_number, message_id, sender_qqnumber, "正在群发... 目标:{}个群".format(len(s)))
                    for i in s:
                        sendGroupmsg2(i, " ".join(command_list[2:]))
                        time.sleep(random.randint(500, 800)/1000)
                    sendGroupmsg(group_number, message_id, sender_qqnumber, "群发完成")
                else:
                    sendGroupmsg2(command_list[1], " ".join(command_list[2:]))
            else:
                sendGroupmsg5(group_number, message_id, sender_qqnumber, "你的权限不足!")

        if command_list[0] == "#mute":
            if sender_qqnumber in ADMIN_LIST:
                if command_list[1] == "all":
                    sendGroupmsg3(group_number, sender_qqnumber,
                                  "尝试在所有群禁言 {} {}分钟...".format(command_list[2], command_list[3]))
                    s = getGroups()
                    print(s)
                    command_list[3] = int(command_list[3])
                    for i in s:
                        if command_list[3] == 0:
                            unmutePerson(i, command_list[2])
                        else:
                            mutePerson(i, command_list[2], command_list[3] * 60)
                        time.sleep(random.randint(500, 800)/1000)
                    sendGroupmsg3(group_number, sender_qqnumber,
                                  "已在所有群禁言 {} {}分钟...".format(command_list[2], command_list[3]))
                else:
                    if command_list[1] == "this":
                        command_list[1] = group_number
                    else:
                        command_list[1] = int(command_list[1])
                    command_list[2] = int(command_list[2].replace("@", ""))
                    command_list[3] = int(command_list[3])
                    if command_list[3] == 0:
                        unmutePerson(command_list[1], command_list[2])
                    else:
                        mutePerson(command_list[1], command_list[2], command_list[3] * 60)
                        sendGroupmsg3(group_number, sender_qqnumber,
                                      "已尝试在群 {} 禁言 {} {}分钟".format(command_list[1], command_list[2], command_list[3]))
            else:
                sendGroupmsg5(group_number, message_id, sender_qqnumber, "你的权限不足!")
        
        if command_list[0] == "#namelocker":
            if sender_qqnumber not in ADMIN_LIST:
                sendGroupmsg5(group_number, message_id, sender_qqnumber, "你的权限不足!")
                return
            if command_list[1] == "list":
                temp1 = ""
                for i in NICKNAME_LOCKED:
                    temp1 += "{} 在群 {} 的名称被锁定为: {}\n".format(i[0], i[1], i[2])
                sendGroupmsg(group_number, message_id, sender_qqnumber, temp1)
            if command_list[1] == "add":
                if len(command_list) < 5:
                    sendGroupmsg5(group_number, message_id, sender_qqnumber, "正确用法: #namelocker add <群号 (或用this指代本群)> <QQ号> <名称>")
                    return
                command_list[2] = command_list[2].replace("this", str(group_number))
                command_list[2] = int(command_list[2])
                command_list[3] = int(command_list[3])
                for i in range(len(NICKNAME_LOCKED)):
                    if command_list[2] == i[0] and command_list[3] == i[1]:
                        sendGroupmsg5(group_number, message_id, sender_qqnumber, "已存在该对象")
                        return
                NICKNAME_LOCKED.append([command_list(2), command_list[3], " ".join(command_list[4:])])
                sendGroupmsg5(group_number, message_id, sender_qqnumber, "已尝试添加")
            if command_list[1] == "remove":
                command_list[2] = command_list[2].replace("this", str(group_number))
                command_list[2] = int(command_list[2])
                command_list[3] = int(command_list[3])
                for i in range(len(NICKNAME_LOCKED)):
                    if command_list[2] == i[0] and command_list[3] == i[1]:
                        del NICKNAME_LOCKED[i]
                        sendGroupmsg5(group_number, message_id, sender_qqnumber, "已尝试移除")
                        return
                sendGroupmsg5(group_number, message_id, sender_qqnumber, "找不到对象")

        if command_list[0] == "#quit":
            if sender_qqnumber == 1584784496:
                ALLOWRUNNING = False
                sendGroupmsg3(group_number, sender_qqnumber,
                                      "已尝试设置运行信号为False")

        if command_list[0] == "#fdpinfo":
            # https://bstats.org/api/v1/plugins/11076/charts/<Type>/data
            try:
                if command_list[1] == "online":
                    url = "https://bstats.org/api/v1/plugins/11076/charts/minecraftVersion/data"
                    a = requests.get(url=url).json()
                    onlinePlayer = 0
                    for i in a:
                        onlinePlayer += i["y"]
                    sendGroupmsg(group_number, message_id, sender_qqnumber, "[CQ:image,file=base64://"+text2image("OnlinePlayers: {}".format(onlinePlayer))+"]")
                elif command_list[1] == "versions":
                    url = "https://bstats.org/api/v1/plugins/11076/charts/pluginVersion/data"
                    a = requests.get(url=url).json()
                    onlineVersion = []
                    for i in a:
                        onlineVersion.append("{}: {}".format(i["name"], i["y"]))
                    sendGroupmsg(group_number, message_id, sender_qqnumber, 
                                 "[CQ:image,file=base64://"+text2image("OnlineVersionsInfo:\n{}".format("\n".join(onlineVersion)))+"]")
                elif command_list[1] == "systems":
                    url = "https://bstats.org/api/v1/plugins/11076/charts/os/data"
                    a = requests.get(url=url).json()
                    onlineSystem = []
                    for i in a["seriesData"]:
                        onlineSystem.append("{}: {}".format(i["name"], i["y"]))
                    sendGroupmsg(group_number, message_id, sender_qqnumber,
                                 "[CQ:image,file=base64://"+text2image("OnlineSystms:\n{}".format("\n".join(onlineSystem)))+"]")
                elif command_list[1] == "countries":
                    url = "https://bstats.org/api/v1/plugins/11076/charts/location/data"
                    a = requests.get(url=url).json()
                    onlineCountry = []
                    for i in a:
                        onlineCountry.append("{}: {}".format(i["name"].replace("Hong Kong", "Hong Kong, China").replace("Taiwan", "Taiwan, China"),
                            i["y"]))
                    sendGroupmsg(group_number, message_id, sender_qqnumber,
                                 "[CQ:image,file=base64://"+text2image("OnlineCountrys:\n{}".format("\n".join(onlineCountry)))+"]")
                elif command_list[1] == "beta":
                    sendGroupmsg(group_number, message_id, sender_qqnumber, "Please wait...")
                    url = "https://api.github.com/repos/UnlegitMC/FDPClient/actions/runs"
                    a = requests.get(url=url).json()
                    objectIDs = []
                    for i in a["workflow_runs"]:
                        if i["name"] == "build":
                            objectIDs.append(i["id"])
                    actionInfo = requests.get(url="https://api.github.com/repos/UnlegitMC/FDPClient/actions/runs/{}".format(objectIDs[0])).json()
                    updTime = actionInfo["head_commit"]["timestamp"]
                    updMsg = actionInfo["head_commit"]["message"]
                    updAuthor = "{} ({})".format(actionInfo["head_commit"]["author"]["name"], actionInfo["head_commit"]["author"]["email"])
                    sendGroupmsg(group_number, message_id, sender_qqnumber,
                                 "Update Time:{}\n"
                                 "Update Message:{}\n"
                                 "Author:{}\n"
                                 "Download URL:https://nightly.link/UnlegitMC/FDPClient/actions/runs/{}/FDPClient.zip\n".format(updTime, updMsg, updAuthor, objectIDs[0]))
                elif command_list[1] == "release":
                    url = "https://api.github.com/repos/UnlegitMC/FDPClient/releases/latest"
                    a = requests.get(url=url).json()
                    files = []
                    for i in a["assets"]:
                        files.append("{}: {}".format(i["name"], i["browser_download_url"].replace("github.com", "hub.fastgit.org")))
                    sendGroupmsg(group_number, message_id, sender_qqnumber,
                                 "Version: {}\n".format(a["name"])+"\n".join(files))
            except Exception as e:
                getError(group_number, message_id, sender_qqnumber, traceback.format_exc())
    except Exception as e:
        print(traceback.format_exc())


def mutePerson(group, qqnumber, mutetime):
    data1 = {
        "group_id": int(group),
        "user_id": int(qqnumber),
        "duration": int(mutetime)
    }
    print(requests.post("http://" + HTTPURL + "/set_group_ban", data=data1).text)


def unmutePerson(group, qqnumber):
    mutePerson(group, qqnumber, 0)


def recall(msgid):
    data1 = {
        "message_id": int(msgid)
    }
    print(requests.post("http://" + HTTPURL + "/delete_msg", data=data1).text)


def sendGroupmsg2(target1, text):
    data1 = {
        "group_id": int(target1),
        "message": text
    }
    print("[Bot -> Group]{}".format(text))
    print(requests.post("http://" + HTTPURL + "/send_group_msg", data=data1).text)


def sendGroupmsg3(target1, senderqq, text):
    if senderqq in BLACK_LIST:
        return
    sendGroupmsg2(target1, "[CQ:at,qq={}]{}".format(senderqq, text))


def sendGroupmsg(target1, msgid, senderqq, text):
    if senderqq in BLACK_LIST:
        return
    sendGroupmsg2(target1, "[CQ:reply,id={}][CQ:at,qq={}]{}".format(msgid, senderqq, text))


def sendGroupmsg5(target1, msgid, senderqq, text):
    if senderqq in BLACK_LIST:
        return
    sendGroupmsg(target1, msgid, senderqq, text)


def sendGroupmsgImg(target1, msgid, senderqq, base64s):
    sendGroupmsg(target1, msgid, senderqq, "[CQ:image,file=base64://{}]".format(base64s))


def sendGuildmsg(guild_id, channel_id, message_id, sender_id, message):
    data1 = {
        "guild_id": guild_id,
        "channel_id": channel_id,
        "message": "[CQ:reply,id={}][CQ:at,qq={}]".format(message_id, sender_id)+message
    }
    print(requests.post("http://" + HTTPURL + "/send_guild_channel_msg", data=data1).text)


def urlget(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 4 Build/JOP40D) AppleWebKit/535.19 (KHTML, '
                      'like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19'}
    temp = requests.get(url, headers=headers)
    return temp.text


def getError(a1, a2, a3, errorText):
    sendGroupmsg(a1, a2, a3, "很抱歉，我们在执行你的指令时出现了一个问题 =_=\n各指令用法请查看 https://lingbot.guimc.ltd/")
    sendTempMsg(523201000, 1584784496, errorText)


def sendTempMsg(target1, target2, text):
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


def permCheck(groupID: int, target: int):
    return True


def nickname(group:int, target:int, nick:str):
    data1 = {
        "group_id": group,
        "user_id": target,
        "card": nick
    }
    print(requests.post(url = "http/{}/set_group_card".format(HTTPURL), data=data1))


# 定义一个用来接收监听数据的方法
def on_message(ws, message):
    threading.Thread(target=on_message2, args=(ws, message)).start()


# 定义一个用来处理错误的方法
def on_error(ws, error):
    print("-----连接出现异常,异常信息如下-----")
    print(error)


# 定义一个用来处理关闭连接的方法
def on_close(ws, a, b):
    print("-------连接已关闭------")


def updatet(a):
    # print("s1")
    while True:
        try:
            if time.strftime("%H:%M:%S", time.localtime()) == "23:00:00":
                sendGroupmsg2("523201000",
                              "夜深了,好好休息一下吧!\n\n" + requests.get("http://api.muxiuge.cn/API/society.php").json()[
                                  "text"] + "\n" + requests.get("http://open.iciba.com/dsapi/").json()["content"] + "\n" +
                              requests.get("http://open.iciba.com/dsapi/").json()["note"])
            if time.strftime("%H:%M:%S", time.localtime()) == "8:00:00":
                sendGroupmsg2("523201000", "王⑧抄们的早上好!\n\n" + requests.get("http://api.muxiuge.cn/API/society.php").json()[
                    "text"] + "\n" + requests.get("http://open.iciba.com/dsapi/").json()["content"] + "\n" +
                          requests.get("http://open.iciba.com/dsapi/").json()["note"])
            if time.strftime("%H:%M:%S", time.localtime()) == "21:35:00":
                sendGroupmsg2("523201000",
                              "王⑧抄们的每日Ban快报:\n" + requests.get("http://api.xgstudio.xyz/hypban.php?type=bans") + "\n\n" +
                              requests.get("http://api.muxiuge.cn/API/society.php").json()["text"] + "\n" +
                              requests.get("http://open.iciba.com/dsapi/").json()["content"] + "\n" +
                              requests.get("http://open.iciba.com/dsapi/").json()["note"])
            if time.strftime("%H:%M:%S", time.localtime()) == "7:00:05":
                sendGroupmsg2("523201000", "来一份涩图开始美好的一天吧!")
                sendGroupmsgImg("523201000", "0", "2734583",
                            base64.b64encode(requests.get("http://www.xgstudio.xyz/api").content).decode())
            if time.strftime("%H:%M:%S", time.localtime()) == "12:00:00":
                sendGroupmsg2("523201000", "王⑧抄们的中午好!\n\n" + requests.get("http://api.muxiuge.cn/API/society.php").json()[
                    "text"] + "\n" + requests.get("http://open.iciba.com/dsapi/").json()["content"] + "\n" +
                              requests.get("http://open.iciba.com/dsapi/").json()["note"])
        except KeyboardInterrupt:
            quit()
        except:
            pass
        time.sleep(0.1)


def githubSub():
    # print("s2")
    url = "https://api.github.com/repos/UnlegitMC/FDPClient/actions/runs"
    newest = None
    try:
        a = requests.get(url=url).json()
        objectIDs = []
        for i in a["workflow_runs"]:
            if i["name"] == "build":
                objectIDs.append(i["id"])
        print(objectIDs)
        newest = objectIDs[0]
        # sendGroupmsg2(523201000, "开始为本群监听 FDPClient 的 actions")
    except:
        print("github请求失败", url)
        print(traceback.format_exc())
    while True:
        try:
            a = requests.get(url=url).json()
            objectIDs = []
            for i in a["workflow_runs"]:
                if i["name"] == "build":
                    objectIDs.append(i["id"])
            if objectIDs[0] != newest:
                newest = objectIDs[0]
                actionInfo = requests.get(url="https://api.github.com/repos/UnlegitMC/FDPClient/actions/runs/{}".format(objectIDs[0])).json()
                updTime = actionInfo["head_commit"]["timestamp"]
                updMsg = actionInfo["head_commit"]["message"]
                updAuthor = "{} ({})".format(actionInfo["head_commit"]["author"]["name"], actionInfo["head_commit"]["author"]["email"])
                sendGroupmsg2(523201000,
                             "监听到 FDPClient 的 actions 有新的任务\nUpdate Time:{}\n"
                             "Update Message:{}\n"
                             "Author:{}\n"
                             "Download URL:https://nightly.link/UnlegitMC/FDPClient/actions/runs/{}/FDPClient.zip\n".format(updTime, updMsg, updAuthor, objectIDs[0]))
        except KeyboardInterrupt:
            quit()
        except:
            pass
        time.sleep(60)


def nickname_locker():
    while True:
        for i in NICKNAME_LOCKED:
            try:
                nickname(i[0], i[1], i[2])
            except Exception as e:
                print(traceback.format_exc(e))
        time.sleep(30)


def main():
    # TODO: 将所有函数分类 (咕咕咕 咕咕咕)
    try:
        print("Starting... (0/6)")
        readConfig()
        print("Starting... (1/6)")
        t1 = threading.Thread(target=updatet, args=("a"))
        t2 = threading.Thread(target=githubSub)
        ws = websocket.WebSocketApp("ws://" + WSURL + "/all?verifyKey=uThZyFeQwJbD&qq=3026726134",
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close,
                                    )
        t3 = threading.Thread(target=ws.run_forever)
        t4 = threading.Thread(target=nickname_locker)
        t1.daemon = True
        t2.daemon = True
        t3.daemon = True
        t4.daemon = True
        print("Starting... (2/6)")
        t1.start()
        print("Starting... (3/6)")
        t2.start()
        print("Starting... (4/6)")
        t3.start()
        print("Starting... (5/6)")
        t4.start()
        print("Starting... (6/6)")
        print("Bot Ready!")
        while ALLOWRUNNING:
            time.sleep(1)
        quit()
    except KeyboardInterrupt:
        quit()
    except Exception:
        print("遇到无法恢复的错误 即将退出")
        print(traceback.format_exc())
        quit()

main()
