import re

from utils.qqbot import sendMessage


def on_message(msg, command_list):
    global INTRODUCE, ADMIN_LIST
    if msg.sender.id in INTRODUCE['waiting']:
        atcq = re.search(r'\[CQ:at,qq=(.*)]', msg.text)
        if atcq is not None:
            command_list = msg.text.replace("[CQ:at,qq={}]".format(atcq.group(1)), str(atcq.group(1))).split(
                " ")
        INTRODUCE["waiting"].remove(msg.sender.id)
        if command_list[0].isdigit() or command_list[0] == 'me':
            if command_list[0] == 'me':
                command_list[0] = str(msg.sender.id)
            if str(command_list[0]) in INTRODUCE['qq']:
                if str(msg.group.id) in INTRODUCE['qq'][str(command_list[0])]:
                    sendMessage(f"的介绍为 : \n{INTRODUCE['qq'][str(command_list[0])][str(msg.group.id)]}",
                                command_list[0], msg.group.id)
                else:
                    sendMessage(f"未在此群添加介绍", command_list[0], msg.group.id)
            else:
                sendMessage(f"未在任何群添加介绍", command_list[0], msg.group.id)
        else:
            msg.fast_reply("请发送QQ号或'me'!!!")
        return

    if command_list[0] == "!introduce" or command_list[0] == "!介绍":
        atcq = re.search(r'\[CQ:at,qq=(.*)]', msg.text)
        if atcq is not None:
            command_list = msg.text.replace("[CQ:at,qq={}]".format(atcq.group(1)), str(atcq.group(1))).split(
                " ")
        introduce = msg.text
        if len(command_list) == 1:
            msg.fast_reply("您想看谁的介绍呢？")
            INTRODUCE['waiting'].append(msg.sender.id)
        elif command_list[1] == 'help':
            msg.fast_reply(f"""
    介绍指令 : !introduce/!介绍
    编辑介绍 :
        使用方法 :
            发送“!introduce/!介绍 <type> <群号> <介绍>”
        <type> : add(添加) remove(删除) edit(编辑)
        <群号> : 如果在本群可以填"this"
        <介绍> : 随便填（支持CQ码）
    查看介绍 : 
        发送“!introduce/!介绍 <Q号>” 
        <Q号> : 填"me"介绍自己
    超管功能 ： 
        可编辑某人的介绍
        使用方法 : !introduce/!介绍 edit_sb <Q号> <群号> <介绍>
    """, reply=False, at=False)
        elif command_list[1] == "empty":
            if msg.sender.isadmin():
                INTRODUCE["qq"] = {}
                INTRODUCE["waiting"] = []
                msg.fast_reply("已清空所有人的介绍")
            else:
                msg.fast_reply("您的权限不足")
        elif len(command_list) == 2 and (command_list[1].isdigit() or command_list[1] == 'me'):
            if command_list[1] == 'me':
                command_list[1] = str(msg.sender.id)
            if str(command_list[1]) in INTRODUCE['qq']:
                if str(msg.group.id) in INTRODUCE['qq'][str(command_list[1])]:
                    sendMessage(f"的介绍为 : \n{INTRODUCE['qq'][str(command_list[1])][str(msg.group.id)]}",
                                command_list[1], msg.group.id)
                else:
                    sendMessage(f"未在此群添加介绍", command_list[1], msg.group.id)
            else:
                sendMessage(f"未在任何群添加介绍", command_list[1], msg.group.id)
        elif len(command_list) >= 3:
            if command_list[2] == "this":
                command_list[2] = str(command_list[2])
            if command_list[1] == "add":
                if str(msg.sender.id) in INTRODUCE['qq']:
                    if str(msg.group.id) in INTRODUCE['qq'][str(msg.sender.id)]:
                        msg.fast_reply("您已经在这个群添加过介绍了，若要编辑请把add改为edit" if command_list[2] == str(
                            msg.group.id) else f"您已经在群{command_list[2]}添加过介绍了，")
                    else:
                        introduce = introduce.replace(f"{command_list[0]} {command_list[1]} ", '')
                        introduce = introduce.replace(f"{command_list[2]} ", '')
                        introduce = introduce.replace("this ", '')
                        INTRODUCE['qq'][str(msg.sender.id)][str(msg.group.id)] = introduce
                        msg.fast_reply("添加成功")
                else:
                    INTRODUCE['qq'][str(msg.sender.id)] = {}
                    introduce = introduce.replace(f"{command_list[0]} {command_list[1]} ", '')
                    introduce = introduce.replace(f"{command_list[2]} ", '')
                    introduce = introduce.replace("this ", '')
                    INTRODUCE['qq'][str(msg.sender.id)][str(msg.group.id)] = introduce
                    msg.fast_reply("添加成功")
            if command_list[1] == "remove":
                if str(msg.sender.id) in INTRODUCE['qq']:
                    if str(msg.group.id) in INTRODUCE['qq'][str(msg.sender.id)]:
                        del INTRODUCE['qq'][str(msg.sender.id)][str(msg.group.id)]
                        msg.fast_reply(
                            "已删除您在本群的介绍" if command_list[2] == str(msg.group.id) else f"已删除您在群{command_list[2]}的介绍")
                    else:
                        msg.fast_reply("您还未在此群添加介绍，请先把remove改为add添加后重试" if command_list[2] == str(
                            msg.group.id) else f"您还未在群{command_list[2]}添加介绍，请先把remove改为add添加后重试")
                else:
                    msg.fast_reply("您还未在任何群添加介绍，请先把remove改为add添加后重试")
            if command_list[1] == "edit":
                if str(msg.sender.id) in INTRODUCE['qq']:
                    if str(msg.group.id) in INTRODUCE['qq'][str(msg.sender.id)]:
                        introduce = introduce.replace(f"{command_list[0]} {command_list[1]} ", '')
                        introduce = introduce.replace(f"{command_list[2]} ", '')
                        introduce = introduce.replace("this ", '')
                        INTRODUCE['qq'][str(msg.sender.id)][str(msg.group.id)] = introduce
                        msg.fast_reply(
                            "已修改您在本群的介绍" if command_list[2] == str(msg.group.id) else f"已修改您在群{command_list[2]}的介绍")
                    else:
                        msg.fast_reply("您还未在此群添加介绍,请把edit改为add重试" if command_list[2] == str(
                            msg.group.id) else f"您还未在群{command_list[2]}添加介绍,请把edit改为add重试")
                else:
                    msg.fast_reply("您还未在任何群添加介绍")
            if command_list[1] == "edit_sb":
                if msg.sender.isadmin():
                    if command_list[3] == "this":
                        command_list[3] = str(msg.group.id)
                    introduce = introduce.replace(f"{command_list[0]} {command_list[1]} {command_list[2]} ", '')
                    introduce = introduce.replace(f"{command_list[3]} ", '')
                    introduce = introduce.replace("this ", '')
                    if command_list[2] not in INTRODUCE["qq"]:
                        INTRODUCE["qq"][command_list[2]] = {}
                    if int(command_list[2]) not in ADMIN_LIST:
                        INTRODUCE["qq"][command_list[2]][command_list[3]] = introduce
                        msg.fast_reply(f"已修改{command_list[2]}在本群的介绍" if command_list[3] == str(
                            msg.group.id) else f"已修改{command_list[2]}在群{command_list[3]}的介绍")
                    else:
                        msg.fast_reply("不可编辑超管的介绍！！")
                else:
                    msg.fast_reply("权限不足！！")