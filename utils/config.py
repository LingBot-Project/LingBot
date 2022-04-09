import configparser
import json

from utils.qqbot import sendMessage


def read_config():
    config = configparser.ConfigParser()
    config.read("config.ini")
    s = config["DEFAULT"]
    try:
        admin_list = [int(i) for i in s["admin"].split(",")]
    except:
        pass
    try:
        black_list = [int(i) for i in s["blacklist"].split(",")]
    except:
        pass
    introduce = {}
    accomplishment = {}
    try:
        with open('json_list.txt', mode="r", encoding="UTF-8") as jsonfile:
            json_list = json.loads(jsonfile.read())
            introduce["qq"] = json_list["INTRODUCE"]
            accomplishment["qq"] = json_list["ACCOMPLISHMENT"]
    except:
        pass

    config.read("verify.ini")
    try:
        verified = config["VERIFIED"]
    except:
        pass
    sendMessage("restart successful", target_group=1019068934)

    return admin_list, black_list, verified, introduce, accomplishment


def save_config(admin_list, black_list, verified, introduce, accomplishment):
    config = configparser.ConfigParser()
    config["DEFAULT"] = {
        "admin": ",".join('%s' % _id for _id in admin_list),
        "blacklist": ",".join('%s' % _id for _id in black_list)
    }
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    json_list = {
        "INTRODUCE": introduce['qq'],
        "ACCOMPLISHMENT": accomplishment['qq']
    }
    with open('json_list.txt', 'w', encoding='UTF-8') as jsonfile:
        jsonfile.write(json.dumps(json_list))
    config = configparser.ConfigParser()
    config["VERIFIED"] = verified
    with open("verify.ini", 'w') as configfile:
        config.write(configfile)