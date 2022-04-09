import requests


def on_message(msg, command_list):
    if command_list[0] == "!music":
        # Netease API: http://cloud-music.pl-fe.cn/search?keywords={" ".join(command_list[1:])}
        search_result = requests.get(
            url=f'http://cloud-music.pl-fe.cn/search?keywords={" ".join(command_list[1:])}').json()
        if search_result["code"] != 200:
            msg.fast_reply(f"搜索失败! {search_result['code']}")
            return

        msg.fast_reply("这是你要找的歌吗?")
        msg.fast_reply(f"[CQ:music,type=163,id={search_result['result']['songs'][0]['id']}]")