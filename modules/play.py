import requests

from utils.image import text2image
from utils.qqbot import mutePerson, sendMessage, mute_type

AUTISM = []


def on_message(msg, command_list):
    global AUTISM
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

    if command_list[0] == "!fdpinfo":
        if command_list[1] == "online":
            url = "https://bstats.org/api/v1/plugins/11076/charts/minecraftVersion/data"
            a = requests.get(url=url).json()
            onlinePlayer = 0
            for i in a:
                onlinePlayer += i["y"]
            msg.fast_reply("[CQ:image,file=base64://" + text2image("OnlinePlayers: {}".format(onlinePlayer)) + "]")
        elif command_list[1] == "versions":
            url = "https://bstats.org/api/v1/plugins/11076/charts/pluginVersion/data"
            a = requests.get(url=url).json()
            onlineVersion = []
            for i in a:
                onlineVersion.append("{}: {}".format(i["name"], i["y"]))
            msg.fast_reply("[CQ:image,file=base64://" + text2image(
                "OnlineVersionsInfo:\n{}".format("\n".join(onlineVersion))) + "]")
        elif command_list[1] == "systems":
            url = "https://bstats.org/api/v1/plugins/11076/charts/os/data"
            a = requests.get(url=url).json()
            onlineSystem = []
            for i in a["seriesData"]:
                onlineSystem.append("{}: {}".format(i["name"], i["y"]))
            msg.fast_reply(
                "[CQ:image,file=base64://" + text2image("OnlineSystms:\n{}".format("\n".join(onlineSystem))) + "]")
        elif command_list[1] == "countries":
            url = "https://bstats.org/api/v1/plugins/11076/charts/location/data"
            a = requests.get(url=url).json()
            onlineCountry = []
            for i in a:
                onlineCountry.append("{}: {}".format(
                    i["name"].replace("Hong Kong", "Hong Kong, China").replace("Taiwan", "Taiwan, China"),
                    i["y"]))
            msg.fast_reply("[CQ:image,file=base64://" + text2image(
                "OnlineCountrys:\n{}".format("\n".join(onlineCountry))) + "]")
        elif command_list[1] == "beta":
            msg.fast_reply("Please wait...")
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
            msg.fast_reply("Update Time:{}\n"
                           "Update Message:{}\n"
                           "Author:{}\n"
                           "Download URL:https://nightly.link/UnlegitMC/FDPClient/actions/runs/{}/FDPClient.zip\n".format(
                upd_time, updMsg, updAuthor, objectIDs[0]))
        elif command_list[1] == "release":
            url = "https://api.github.com/repos/UnlegitMC/FDPClient/releases/latest"
            a = requests.get(url=url).json()
            files = []
            for i in a["assets"]:
                files.append(
                    "{}: {}".format(i["name"], i["browser_download_url"].replace("github.com", "hub.fastgit.org")))
            msg.fast_reply("Version: {}\n".format(a["name"]) + "\n".join(files))