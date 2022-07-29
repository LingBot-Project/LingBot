import base64
import random

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from flask import Flask
from flask import request
import os

app = Flask(__name__)


def join_images(png1, png2, size=0):
    """
    图片拼接
    :param png1: 图片1
    :param png2: 图片2
    :param size: 两个图片重叠的距离
    :param output: 输出的图片文件
    :return:
    """
    # 图片拼接
    img1, img2 = Image.open(png1), Image.open(png2)
    size1, size2 = img1.size, img2.size  # 获取两张图片的大小
    joint = Image.new('RGB', (size1[0], size1[1] + size2[1] - size))  # 创建一个空白图片
    # 设置两张图片要放置的初始位置
    loc1, loc2 = (0, 0), (0, size1[1] - size)
    # 分别放置图片
    joint.paste(img1, loc1)
    joint.paste(img2, loc2)
    # 保存结果
    joint.save(png1)


def screenshot(url: str, img_path: str) -> None:
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument("-lang=zh-cn")
    driver1 = webdriver.Chrome(chrome_options=chrome_options, executable_path="/root/chromedriver")
    driver1.get(url)
    # 获取body大小
    body_h = int(driver1.find_element_by_xpath('//body').size.get('height'))
    body_w = int(driver1.find_element_by_xpath('//body').size.get('width'))
    driver1.set_window_size(body_w+150, body_h+30)

    driver1.save_screenshot(img_path)
    driver1.close()
    driver1.quit()


def get_base64_by_url(url: str) -> str:
    random_id = random.randint(1000000, 9999999)
    screenshot(url=url, img_path=f"{random_id}.cache.png")
    with open(f"{random_id}.cache.png", 'rb') as f:
        return base64.b64encode(f.read()).decode()


@app.route("/url2base64", methods=['POST'])
def flask_task1():
    url = request.form['url']
    return get_base64_by_url(url)


if __name__ == "__main__":
    app.run(debug=False, port=25666)