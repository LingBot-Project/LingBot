import base64
import random
import re
from io import BytesIO

import requests
from PIL import Image

from utils import five_k_utils
from utils.image import mask_sircle_transparent


def on_message(msg, command_list):
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
        imb, mask1 = mask_sircle_transparent(ima.rotate(-160), 0, 2)
        imc.paste(imb, (19, 181), mask=mask1)
        _temp = BytesIO()
        imc.save(_temp, format="PNG")
        msg.fast_reply("[CQ:image,file=base64://{}]".format(base64.b64encode(_temp.getvalue()).decode()))

    if command_list[0] == "!5k":
        # 图片/灵感来源: https://github.com/SAGIRI-kawaii/saya_plugins_collection/tree/master/modules/5000zhao
        # 字体文件: ./5k_fonts
        imageuid = str(random.randint(10000000, 9999999999))
        five_k_utils.genImage(word_a=command_list[1], word_b=command_list[2]).save(imageuid + ".cache.png")
        with open(imageuid + ".cache.png", "rb") as f:
            msg.fast_reply("[CQ:image,file=base64://{}]".format(base64.b64encode(f.read()).decode()))