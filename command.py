# -*- coding: UTF-8 -*-
"""TODO 留个悬念(其实是我没想好怎么写)"""
import os

COMMAND_LIST = []
COMMAND_DICT = {}


class Command:
    def __init__(self):
        # TODO: 遍历commands下的每一个py文件(__init__除外)，将文件的name和 func这个函数的地址添加到列表和字典中
        for _, _, file_names in os.walk("commands/"):
            for i in file_names:
                if i[-3:] == ".py":
                    p = i[:-3]
                    if p == "__init__":
                        continue
                    try:
                        f = open(f"commands/{i}", "r", encoding="utf-8")

                        print(f"tried to load: {p}")
                        exec(f.read() + '\nCommand.add_command(COMMAND, func)')

                        f.close()
                    except Exception as exc:
                        print(f"here are some problems in loading command: {p}'s function, {exc}")
            pass

    @staticmethod
    def add_command(name: str = '', func: any = None) -> None:
        """
        :param name: the command's name
        :param func: function
                     func:def func(sender: Message) -> None:
        """
        COMMAND_LIST.append(name)
        COMMAND_DICT[name] = func

    @staticmethod
    def get_function(name: str) -> any:
        """
        :param name: the command's name
        :return: return the func of the name in dict
        """
        return COMMAND_DICT.get(name)

if __name__ == '__main__':
    c = Command()
