from PIL import Image, ImageDraw, ImageFont
import random, base64, requests, traceback
from moduleManager import *

def text2image(text):
    imageuid = str(random.randint(10000000, 9999999999))
    fontSize = 22
    max_w = 0
    lines = text.split('\n')
    # print(len(lines))
    fontPath = r"/root/LingBot/a.ttf"
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


def acg_img():
    try:
        a = "https://img.xjh.me/random_img.php?return=json"
        a1 = requests.get(url=a).json()
        return base64.b64encode(requests.get(url='https:' + a1["img"]).content).decode()
    except Exception as e:
        return text2image("获取图片失败\n" + traceback.format_exc())

@ModuleManager.module("二次元")
def acg(msg, _):
    msg.fastReply("[CQ:image,file=base64://" + acg_img() + "]")

@ModuleManager.module("一英")
def one_eng(msg, _):
    a = requests.get("http://open.iciba.com/dsapi/").json()
    msg.fastReply(f'{a["content"]}\n{a["note"]}')