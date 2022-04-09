import requests

from utils.image import acg_img


def on_message(msg, command_list):
    if msg.text == "一语":
        msg.fast_reply(requests.get("http://api.muxiuge.cn/API/society.php").json()["text"])

    if msg.text == "一英":
        msg.fast_reply(requests.get("http://open.iciba.com/dsapi/").json()["content"] + "\n" +
                       requests.get("http://open.iciba.com/dsapi/").json()["note"])

    if msg.text == "二次元":
        msg.fast_reply("[CQ:image,file=base64://" + acg_img() + "]")

    # if msg.text == "必应壁纸":
    #     msg.fast_reply("[CQ:image,file=base64://" + base64.b64encode(
    #         requests.get("http://www.xgstudio.xyz/api/bing.php").content).decode() + "]")

    if msg.text == "一话":
        req1 = requests.get("http://open.iciba.com/dsapi/").json()
        msg.fast_reply(
            requests.get("http://api.muxiuge.cn/API/society.php").json()["text"])
        msg.fast_reply(req1["content"] + "\n" + req1["note"])