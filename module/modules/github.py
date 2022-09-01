import json
import random
import threading
import traceback
import re
import requests

import bot_state
import time, datetime
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
git_link = re.compile(r'(git|https|git@)(://|)github.com([:/]).*/.*(.git|/| |)')
github_head = re.compile(r'(git|https|git@)(://|)github.com([:/])')
s = """[GitHub]
Repo: {repo}
Description: {description}
Owner: {owner_login}
Default Branch: {branch}
Language: {lang}
Last Commit: {last_commit} ({commit_id})
Create Time: {created_at}
Update Time: {pushed_at}
"""  # Thanks lgz-bot


def find_git_link(string: str):
    a = re.search(git_link, string)
    if a is None:
        return ""
    a= a.span()
    return re.sub(github_head, "", convert_url(string[a[0]: a[1]]))


def github_url_listener(event: GroupMessageEvent):
    global is_in_limit, s
    if bot_state.x_ratelimit_remaining == 0:
        return
    i = find_git_link(event.get_message().text)
    if i == "":
        return
    req = requests.get(f"https://api.github.com/repos/{i}")
    bot_state.x_ratelimit_remaining = int(req.headers["x-ratelimit-remaining"])
    if int(req.headers["x-ratelimit-remaining"]) == 0:
        is_in_limit = True
        return
    c_req = requests.get(f"https://api.github.com/repos/{i}/commits")
    if int(c_req.headers["x-ratelimit-remaining"]) == 0:
        is_in_limit = True
        last_commit = "undefined"
        commit_sha = "undefined"
    else:
        c_req = c_req.json()
        last_commit = c_req[0]["commit"]["message"]
        commit_sha = c_req[0]["sha"]
    rej = req.json()
    event.reply("""[GitHub]
Repo: {repo}
Description: {description}
Owner: {owner_login}
Default Branch: {branch}
Language: {lang}
Latest Commit: {last_commit} ({commit_sha})
Create Time: {created_at}
Update Time: {pushed_at}
""".format(
        repo=i,
        description=rej["description"],
        owner_login=rej["owner"]["login"],
        branch=rej["default_branch"],
        lang=rej["language"],
        last_commit=last_commit,
        commit_sha=commit_sha,
        created_at=parse_ISO_time(rej["created_at"]),
        pushed_at=parse_ISO_time(rej["pushed_at"])
    ))
    pass


def on_msg(event):
    global last_info, api, web_page, listener_last_info, is_in_limit, last_message
    if event.get_commands()[0] != "!git":
        return
    
    if is_in_limit and len(event.get_commands()) == 1:
        event.get_message().fast_reply(f"API rate limit exceeded, please wait for some minutes. Last auto-sync commit info:\n{last_message}")
        return
    
    if len(event.get_commands()) > 1:
        for i in range(1, len(event.get_commands())):
            if not is_in_limit:
                
                github_url_listener(GroupMessageEvent(Message.Message(json.dumps(
                    {  # 构建数据 (草 我为什么要自己构建)
                        "post_type": "message",
                        "message_type": "group",
                        "message": event.get_commands()[i],
                        "sender": {
                            "user_id": event.get_message().sender.id,
                            "nickname": event.get_message().sender.name
                        },
                        "group_id": event.get_message().group.id,
                        "message_id": event.get_message().id
                    }
                ))))
                time.sleep(random.randint(1000, 5000) / 1000)  # sb Tencent, why you blocked bot?
            else:
                break
            # end if
        # end for
        return
    # end if

    # 发送请求，获取数据
    commit_info = requests.get(commit_api)
    bot_state.x_ratelimit_remaining = int(commit_info.headers["x-ratelimit-remaining"])
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
    last_message = f'''
Latest Commit:
repos: {commit_info[0]["html_url"]},
time: {parse_ISO_time(commit_info[0]["commit"]["author"]["date"])},
author: {commit_info[0]["commit"]["author"]["name"]},
message: {commit_info[0]["commit"]["message"]},
sha: {commit_info[0]["sha"]},
pylint check: {get_pylint_state()}
'''
    event.get_message().fast_reply(last_message)

    # last_info = str(cur_update)


def sch_github_listener():
    global listener_last_info, last_info, api, is_in_limit, last_message
    time.sleep(random.randint(500, 2050) / 1000)
    try:
        commit_info = requests.get(commit_api)
        bot_state.x_ratelimit_remaining = int(commit_info.headers["x-ratelimit-remaining"])
        if int(commit_info.headers["x-ratelimit-remaining"]) == 0:
            is_in_limit = True
            raise Exception("API rate limit exceeded")
        commit_info = commit_info.json()
        bot_state.cur_git_ver = commit_info[0]["sha"][:7]
        last_info = commit_info[0]["commit"]["author"]["date"]
        listener_last_info = last_info
    except Exception as e:
        Message.sendMessage(f"[GitHub commit listener] Exception found while trying synchronizing: {e}",
                            target_group=1019068934)
    time.sleep(random.randint(600, 1500) / 1000)
    Message.sendMessage(
        f"[GitHub commit listener] Listener thread is running, current git version: {bot_state.cur_git_ver}, current auto-sync commit time: {parse_ISO_time(listener_last_info)}",
        target_group=1019068934, bypass=True)
    commit_info = {}
    time.sleep(30)
    while bot_state.state:
        time.sleep(random.randint(50000, 81642) / 1000 + (600 if is_in_limit else 0))
        is_in_limit = False
        try:
            # 发送请求，获取数据
            commit_info = requests.get(commit_api)
            bot_state.x_ratelimit_remaining = int(commit_info.headers["x-ratelimit-remaining"])
            if int(commit_info.headers["x-ratelimit-remaining"]) == 0:
                is_in_limit = True
                Message.sendMessage("[GitHub commit listener] Synchronization failed: API rate limit exceeded.",
                                    target_group=1019068934)
                continue
            
            if int(commit_info.headers["x-ratelimit-remaining"]) <= 5:
                is_in_limit = True
            commit_info = commit_info.json()

            # 解析想要的数据，并打印
            cur_update = commit_info[0]["commit"]["author"]["date"]

            if str(listener_last_info) != str(cur_update):
                time.sleep(7)  # wait for pylint's check lol
                # {json.dumps(all_info, sort_keys=True, indent=4, separators=(',', ': '))}
                last_message = f'''commit info: {commit_info[0]["html_url"]}
time: {parse_ISO_time(cur_update)}
author: {commit_info[0]["commit"]["author"]["name"]}
message: {commit_info[0]["commit"]["message"]}
sha: {commit_info[0]["sha"]}
pylint check: {get_pylint_state()}
'''
                _tmp_msg = f"[GitHub] 有新Commit\n{last_message}"
                Message.sendMessage(_tmp_msg, target_group=1019068934)
                time.sleep(random.randint(200, 2250) / 1000)
                Message.sendMessage(_tmp_msg, target_group=308089090)
                listener_last_info = str(cur_update)
                time.sleep(10)  # cool down
        except Exception as _:
            Message.sendMessage(
                f"Found an exception when try to auto-sync github commit: {traceback.format_exc()}, request: {json.dumps(commit_info, sort_keys=True, indent=4, separators=(',', ': '))}",
                target_group=1019068934, bypass=True)


def get_pylint_state():
    return requests.get('https://github.com/LingBot-Project/LingBot/actions/workflows/pylint.yml/badge.svg?event=push').content.decode("UTF-8").split("\n")[1].replace("<title>", "").replace("</title>", "").replace(" ", "")  # Shit code lol


def parse_ISO_time(t: str):
    # time.strptime(t, "%Y%Y%Y%Y-%m%m-%d%dT%H%H:%M%M:%S%SZ")
    return time.asctime(time.localtime(time.mktime(datetime.datetime.strptime(t, "%Y-%m-%dT%H:%M:%S%z").timetuple())+28800))


def convert_url(s: str) -> str:
    drop_len = 0
    if s.endswith("/"):
        drop_len += 1
    if s.endswith(".git"):
        drop_len += 4
    if s.endswith(" "):
        drop_len += 1
    return s[:-drop_len] if drop_len > 0 else s


class GitHubController(IModule):
    def process(self, event: Event):
        if isinstance(event, GroupMessageEvent):
            on_msg(event)
            if event.get_commands()[0] == "!git":
                return
            try:
                github_url_listener(event)
            except:
                pass
        if isinstance(event, BotEnableEvent):
            t1 = threading.Thread(target=sch_github_listener)
            t1.start()
            t1.name = "GithubCommitListener"


if __name__ == '__main__':
    # link = "https://github.com/LingBot-Project/LingBot"
    # sp = re.search(git_link, link).span()
    # print(link[sp[0]:sp[1]])
    # print(find_git_link(link))
    # print(re.sub(github_head, "", link))
    # print("A?")
    # print(convert_url(link))
    # print(convert_url(re.sub(github_head, "", link)))
    print(parse_ISO_time("2022-01-30T09:39:31Z"))
