# -*- coding: UTF-8 -*-
"""TODO 留个悬念(其实是我没想好怎么写)"""

COMMAND_LIST = []
COMMAND_DICT = {}


class Command:
    def __init__(self):
        # TODO: 遍历commands下的每一个py文件(__init__除外)，将文件的name和 func这个函数的地址添加到列表和字典中
        pass

    @staticmethod
    def add_command(name: str = '', func: any = None):
        COMMAND_LIST.append(name)
        COMMAND_DICT[name] = func
