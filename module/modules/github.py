import json
import random
import threading
import traceback

import requests

import bot_state
import time
import utils.Message as Message
from events.Events import *
from module.modules.IModule import IModule

is_in_limit = False
listener_last_info = ""
last_info = ""
last_message = ""
api = 'https://api.github.com/repos/LingBot-Project/LingBot'
commit_api = 'https://api.github.com/repos/LingBot-Project/LingBot/commits'
web_page = "https://github.com/LingBot-Project/LingBot"


def on_msg(event):
    global last_info, api, web_page, listener_last_info, is_in_limit, last_message
    if event.get_commands()[0] != "!git":
        return
    
    if is_in_limit:
        event.get_message().fast_reply(f"API rate limit exceeded, please wait for some minutes. Last auto-sync commit info:\n{last_message}")
        return

    # 发送请求，获取数据
    commit_info = requests.get(commit_api)
    if int(commit_info.headers["x-ratelimit-remaining"]) == 0:
        event.get_message().fast_reply(f"API rate limit exceeded, please wait for some minutes. Last auto-sync commit info:\n{last_message}")
        is_in_limit = True
        return
    commit_info = commit_info.json()

    # # 解析想要的数据，并打印
    # cur_update = all_info['pushed_at']

    # if str(last_info) == str(cur_update):
    #     event.get_message().fast_reply(f"无新Commit\nlast commit: {last_info}\nlast auto-sync commit: {listener_last_info}")
    # else:
    #     event.get_message().fast_reply(f"有新Commit\ntime: {cur_update}\nlast commit: {last_info}\nlast auto-sync commit: {listener_last_info}")
    event.get_message().fast_reply(f'''
Latest Commit:
repos: {commit_info[0]["html_url"]},
time: {commit_info[0]["commit"]["author"]["date"]},
author: {commit_info[0]["commit"]["author"]["name"]},
message: {commit_info[0]["commit"]["message"]},
sha: {commit_info[0]["sha"]}
''')

    # last_info = str(cur_update)


def sch_github_listener():
    global listener_last_info, last_info, api, is_in_limit, last_message
    time.sleep(random.randint(500, 2050) / 1000)
    try:
        all_info = requests.get(api)
        if int(all_info.headers["x-ratelimit-remaining"]) == 0:
            is_in_limit = True
            raise Exception("API rate limit exceeded")
        last_info = all_info.json()['pushed_at']
        listener_last_info = last_info
    except Exception as e:
        Message.sendMessage(f"[GitHub commit listener] Exception found while tring synchronizing: {e}",
                            target_group=1019068934)
    time.sleep(random.randint(600, 1500) / 1000)
    Message.sendMessage(
        f"[GitHub commit listener] Listener thread is running, currect auto-sync commit time: {listener_last_info}",
        target_group=1019068934, bypass=True)
    commit_info = {}
    time.sleep(25)
    while bot_state.state:
        time.sleep(random.randint(42618, 81642) / 1000 + (600 if is_in_limit else 0))
        is_in_limit = False
        try:
            # 发送请求，获取数据
            commit_info = requests.get(commit_api)

            if int(commit_info.headers["x-ratelimit-remaining"]) == 0:
                is_in_limit = True
                Message.sendMessage("[GitHub commit listener] Synchronization failed: API rate limit exceeded.",
                                    target_group=1019068934)
                continue
            commit_info = commit_info.json()

            # 解析想要的数据，并打印
            cur_update = commit_info[0]["commit"]["author"]["date"]

            if str(listener_last_info) != str(cur_update):

                time.sleep(20)  # wait for pylint's check lol
                pylint_pass = requests.get('https://github.com/LingBot-Project/LingBot/actions/workflows/pylint.yml/badge.svg?event=push').content.decode("UTF-8").split("\n")[1].replace("<title>", "").replace("</title>", "").replace(" ", "")  # Shit code lol

                # {json.dumps(all_info, sort_keys=True, indent=4, separators=(',', ': '))}
                last_message = f'''commit info: {commit_info[0]["html_url"]},
time: {cur_update},
author: {commit_info[0]["commit"]["author"]["name"]},
message: {commit_info[0]["commit"]["message"]},
sha: {commit_info[0]["sha"]},
pylint check: {pylint_pass}
'''
                _tmp_msg = f"[GitHub] 有新Commit\n{last_message}"
                Message.sendMessage(_tmp_msg, target_group=1019068934)
                time.sleep(random.randint(200, 2250) / 1000)
                Message.sendMessage(_tmp_msg, target_group=308089090)
                listener_last_info = str(cur_update)
                time.sleep(20)  # cool down
        except Exception as _:
            Message.sendMessage(
                f"Found an exception when try to auto-sync github commit: {traceback.format_exc()}, request: {json.dumps(commit_info, sort_keys=True, indent=4, separators=(',', ': '))}",
                target_group=1019068934, bypass=True)


class GitHubController(IModule):
    def process(self, event: Event):
        if isinstance(event, GroupMessageEvent):
            on_msg(event)
        if isinstance(event, BotEnableEvent):
            t1 = threading.Thread(target=sch_github_listener)
            t1.start()
            t1.name = "GithubCommitListener"
