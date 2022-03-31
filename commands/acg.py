COMMAND = ["一话", "必应壁纸", "二次元", "一语", "一英"]

def acg_img():
    try:
        a = "https://img.xjh.me/random_img.php?return=json"
        a1 = requests.get(url=a).json()
        return base64.b64encode(requests.get(url='https:' + a1["img"]).content).decode()
    except Exception as e:
        return text2image("获取图片失败\n" + traceback.format_exc())


def func(msg, _):
    if msg.text == "一语":
        msg.fastReply(requests.get("http://api.muxiuge.cn/API/society.php").json()["text"])
        
    if msg.text == "一英":
        msg.fastReply(requests.get("http://open.iciba.com/dsapi/").json()["content"] + "\n" +
                      requests.get("http://open.iciba.com/dsapi/").json()["note"])

    if msg.text == "二次元":
        msg.fastReply("[CQ:image,file=base64://" + acg_img() + "]")

    if msg.text == "必应壁纸":
        msg.fastReply("[CQ:image,file=base64://" + base64.b64encode(
            requests.get("http://www.xgstudio.xyz/api/bing.php").content).decode() + "]")

    if msg.text == "一话":
        req1 = requests.get("http://open.iciba.com/dsapi/").json()
        msg.fastReply(
            requests.get("http://api.muxiuge.cn/API/society.php").json()["text"])
        msg.fastReply(req1["content"] + "\n" + req1["note"])  