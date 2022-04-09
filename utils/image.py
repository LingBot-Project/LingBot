import base64
import random
import traceback

import requests
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def crop_max_square(pil_img):
    return crop_center(pil_img, min(pil_img.size), min(pil_img.size))


def crop_center(pil_img, crop_width, crop_height):
    img_width, img_height = pil_img.size
    return pil_img.crop(((img_width - crop_width) // 2,
                         (img_height - crop_height) // 2,
                         (img_width + crop_width) // 2,
                         (img_height + crop_height) // 2))


def mask_sircle_transparent(pil_img, blur_radius, offset=0):
    offset += blur_radius * 2
    mask = Image.new("L", pil_img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((offset, offset, pil_img.size[0] - offset, pil_img.size[1] - offset), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(blur_radius))

    result = pil_img.copy()
    result.putalpha(mask)
    return result, mask


def text2image(text):
    imageuid = str(random.randint(10000000, 9999999999))
    font_size = 22
    max_w = 0
    lines = text.split('\n')
    # print(len(lines))
    font_path = r"a.ttf"
    font = ImageFont.truetype(font_path, font_size)
    for i in lines:
        try:
            if max_w <= font.getmask(i).getbbox()[2]:
                max_w = font.getmask(i).getbbox()[2]
        except:
            pass
    im = Image.new("RGB", (max_w + 11, len(lines) * (font_size + 8)), (255, 255, 255))
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