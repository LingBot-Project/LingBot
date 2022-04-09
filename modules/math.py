import random


def on_message(msg, command_list):
    if msg.text == "!random":
        msg.fast_reply(str(random.randint(1, 100)))
        return

    if command_list[0] == "!plus":
        msg.fast_reply(str(float(command_list[1]) + float(command_list[2])))
        return
    if command_list[0] == "!subtract":
        msg.fast_reply(str(float(command_list[1]) - float(command_list[2])))
        return
    if command_list[0] == "!multiply":
        msg.fast_reply(str(float(command_list[1]) * float(command_list[2])))
        return
    if command_list[0] == "!divide":
        if int(command_list[2]) == 0:
            msg.fast_reply("零不能作除数哦~")
            return
        msg.fast_reply(str(float(command_list[1]) / float(command_list[2])))
        return
