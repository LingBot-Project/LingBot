from events.Events import *
from module.modules.IModule import IModule
import json
import requests
import threading, random
import bot_state, time
import utils.Message as Message

listener_last_info = ""
last_info = ""
api = 'https://api.github.com/repos/LingBot-Project/LingBot'
commit_api = 'https://api.github.com/repos/LingBot-Project/LingBot/commits'
web_page = "https://github.com/LingBot-Project/LingBot"

def on_msg(event):
    global last_info, api, web_page, listener_last_info
    if event.get_commands()[0] != "!git": return

    # 发送请求，获取数据
    all_info = requests.get(api).json()

    # 解析想要的数据，并打印
    cur_update = all_info['pushed_at']

    if str(last_info) == str(cur_update):
        event.get_message().fast_reply(f"无新Commit\nlast commit: {last_info}\nlast auto-sync commit: {listener_last_info}")
    else:
        event.get_message().fast_reply(f"有新Commit\ntime: {cur_update}\nlast commit: {last_info}\nlast auto-sync commit: {listener_last_info}")
    last_info = str(cur_update)


def sch_github_listener():
    global listener_last_info, last_info, api
    
    last_info = requests.get(api).json()['pushed_at']
    listener_last_info = last_info
    time.sleep(random.randint(1, 5))
    Message.sendMessage(f"[GitHub commit listener] Listener thread is running, currect auto-sync commit time: {listener_last_info}", target_group=1019068934)
    while bot_state.state:
        time.sleep(45)
        try:
            # 发送请求，获取数据
            all_info = requests.get(api).json()

            # 解析想要的数据，并打印
            cur_update = all_info['pushed_at']

            if str(listener_last_info) != str(cur_update):
                commit_info = requests.get(commit_api).json()
                Message.sendMessage(f"""=======[GitHub commit listener]=======
有新Commit
repos: {all_info['html_url']},
time: {cur_update},
author: {commit_info[0]['commit']['author']['name']},
message: {commit_info[0]['commit']['message']},
sha: {commit_info[0]['sha']}
""", target_group=1019068934)  # {json.dumps(all_info, sort_keys=True, indent=4, separators=(',', ': '))}
            listener_last_info = str(cur_update)
        except Exception as e:
            Message.sendMessage(f"Found an exception when try to auto-sync github commit: {e}", target_group=1019068934)


class GitHubController(IModule):
    def process(self, event: Event):
        if isinstance(event, GroupMessageEvent):
            on_msg(event)
        if isinstance(event, BotEnableEvent):
            t1 = threading.Thread(target=sch_github_listener)
            t1.start()
            t1.name = "GithubCommitListener"
