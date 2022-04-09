import base64
import json
import logging
import random
import re
from io import BytesIO

import requests
from PIL import Image, ImageFont, ImageDraw

BILI_BV_RE = re.compile(r"BV([a-zA-Z0-9]{10})")


def on_message(msg, command_list):
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