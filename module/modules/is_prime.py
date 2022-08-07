from events.Events import *
from module.modules.IModule import IModule
import math


def is_prime(n):
    if n == 1:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True


class IsPrime(IModule):
    def process(self, event: Event) -> None:
        if isinstance(event, GroupMessageEvent):
            if event.command_list[0] == "!prime":
                if is_prime(int(event.command_list[1])):
                    event.reply("为合数")
                else:
                    event.reply("为素数")
