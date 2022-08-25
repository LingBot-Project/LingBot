from events.Events import *
from module.modules.IModule import IModule
import json
import requests
import threading
import bot_state, time
import utils.Message as Message

listener_last_info = ""
last_info = ""
api = 'https://api.github.com/repos/LingBot-Project/LingBot'
web_page = "https://github.com/LingBot-Project/LingBot"

def on_msg(event):
    global last_info, api, web_page, listener_last_info
    if event.get_commands()[0] != "!git": return

    # 发送请求，获取数据
    all_info = requests.get(api).json()

    # 解析想要的数据，并打印
    cur_update = all_info['updated_at']

    if str(last_info) == str(cur_update):
        event.get_message().fast_reply("无新Commit")
    else:
        event.get_message().fast_reply(f"有新Commit, time: {cur_update}\nlast commit: {last_info}\nlast sync commit: {listener_last_info}")
    last_info = str(cur_update)


def sch_github_listener():
    global listener_last_info, api
    
    listener_last_info = requests.get(api).json()['updated_at']
    while bot_state.state:
        time.sleep(90)
        try:
            # 发送请求，获取数据
            all_info = requests.get(api).json()

            # 解析想要的数据，并打印
            cur_update = all_info['updated_at']

            if str(listener_last_info) != str(cur_update):
                Message.sendMessage(f"""[GITHUB] 有新Commit
time: {cur_update},
{json.dumps(all_info, sort_keys=True, indent=4, separators=(',', ': '))}
""", target_group=1019068934)
            listener_last_info = str(cur_update)
        except Exception as e:
            Message.sendMessage(f"Found an exception when try to sync github commit: {e}")


class GitHubController(IModule):
    def process(self, event: Event):
        if isinstance(event, GroupMessageEvent):
            on_msg(event)
        if isinstance(event, BotEnableEvent):
            t1 = threading.Thread()
            t1.start()
            t1.name = "GithubListener"
