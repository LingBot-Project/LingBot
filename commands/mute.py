COMMAND = "!mute"

def func(msg, command_list):
    if msg.sender.isadmin():
        atcq = re.search(r'\[CQ:at,qq=(.*)]', msg.text)
        if atcq is not None:
            command_list = msg.text.replace("[CQ:at,qq={}]".format(atcq.group(1)), str(atcq.group(1))).split(
                " ")
        if command_list[1] == "this":
            command_list[1] = msg.group.id
        else:
            command_list[1] = int(command_list[1])
        command_list[2] = int(command_list[2].replace("@", ""))
        command_list[3] = int(command_list[3])
        if command_list[3] == 0:
            unmutePerson(command_list[1], command_list[2])
        else:
            mutePerson(command_list[1], command_list[2], command_list[3] * 60)
            msg.fastReply("已尝试在群 {} 禁言 {} {}分钟".format(command_list[1], command_list[2], command_list[3]))
    else:
        msg.fastReply("你的权限不足!")