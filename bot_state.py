# 一个新文件 跟配置文件差不多但又不完全一样(更准确地来说就是个临时存东西的 所有地方都能读的那种 防止循环导入(笑))
state = True
cur_git_ver = "0000000"
x_ratelimit_remaining = 60  # github

command_usage = """帮助 - 指令用法

!help <- 查看机器人的指令用法
!test / 凌状态 <- 获取机器人当前的状态信息

一语 / 一英 / 二次元 / 必应壁纸 / 一话 <- 获取对应内容
!testzb <- 获取每日早报

<!plus / !subtract / !multiply / !divide> <number> <number> <- 加减乘除指定的两个数字
!prime <number> <- 查看数字是否为素数
!random <- 获取从 0 ~ 100 之间的随机数

!丢 <target user> <- 丢出指定用户!
!music <song> <- 搜索音乐
!5k <string> <string> <- 制作5k图片

!hyp players <- 获取Hypixel当前所有游戏的玩家数量
!hyp <player> <- 获取指定玩家在Hypixel的大致信息

!tcping <IP>[:port(default: 80)] <- tcp请求方式获取对应的地址的延迟等信息
!mcping <IP>[:port(default: 25565)] <- 获取对应服务器的图标, motd, 延迟, 在线人数, 版本等信息

!我要自闭 <- 字面意思(笑) 具体用法请使用「!我要自闭 help」查阅
!introduce / !介绍 <- 具体用法请使用「!introduce help / !介绍 help」查阅
!achievements / !成就 <- 具体用法请使用「!achievements help / !成就 help」查阅

!git <- 获取机器人的github仓库当前的状态
!feedback <- 向开发者反馈信息(我们需要您的帮助以提升机器人的使用体验!)
"""
colorful_motd_mapping = {
    "0": "black",
    "1": "dark_blue",
    "2": "dark_green",
    "3": "dark_aqua",
    "4": "dark_red",
    "5": "dark_purple",
    "6": "gold",
    "7": "gray",
    "8": "dark_gray",
    "9": "blue",
    "a": "green",
    "b": "aqua",
    "c": "red",
    "d": "light_purple",
    "e": "yellow",
    "f": "white",
    "g": "minecon_gold",
    # formatting
    "u": "underline",
    "l": "bold",
    "o": "italic",
    "m": "strikethrough",
    "k": "hex",
    "r": "reset"
}
