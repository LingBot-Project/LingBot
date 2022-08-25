from events.Events import *
from module.modules.IModule import IModule
import json
import threading
import bot_state, time

listener_last_info = ""
last_info = ""
api = 'https://api.github.com/repos/LingBot-Project/LingBot'
web_page = "https://github.com/LingBot-Project/LingBot"

def on_msg(event):
    global last_info, api, web_page
    if event.get_commands()[0] != "!git": return


    # 发送请求，获取数据
    all_info = requests.get(api).json()

    # 解析想要的数据，并打印
    cur_update = all_info['updated_at']

    if str(last_info) == str(cur_update):
        msg.fast_reply("无新Commit")
    else:
        msg.fast_reply("有新Commit,time:" + cur_update)
    last_info = str(cur_update)


def sch_github_listener():
    global listener_last_info, api, web_page
    
    listener_last_info = requests.get(api).json()['updated_at']
    while bot_state.state:
        time.sleep(600)
        # 发送请求，获取数据
        all_info = requests.get(api).json()

        # 解析想要的数据，并打印
        cur_update = all_info['updated_at']

        if str(listener_last_info) != str(cur_update):
            msg.fast_reply(f"""[GITHUB] 有新Commit
time: {cur_update},
{json.dumps(all_info, sort_keys=True, indent=4, separators=(',', ': '))}
""")        
        listener_last_info = str(cur_update)


class GitHubController(IModule):
    def process(event: Event):
        if isinstance(event, GroupMessageEvent):
            on_msg(event)
        if isinstance(event, BotEnableEvent):
            t1 = threading.Thread()
            t1.name = "github"
            t1.start()
