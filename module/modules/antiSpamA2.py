from events.Events import *
from module.modules.IModule import IModule
from utils.EvictingList import EvictingList
import time
import utils.mathUtils as mathUtils


TIME_SAMPLES = {}
avg_samples = {}
VLs = {}
times = {}


class AntiSpam(IModule):
    def process(self, event: Event) -> None:
        if isinstance(event, GroupMessageEvent):
            msg = event.get_message()
            if msg.group.id not in TIME_SAMPLES:
                TIME_SAMPLES[msg.group.id] = {}
            if msg.sender.id not in TIME_SAMPLES[msg.group.id]:
                TIME_SAMPLES[msg.group.id][msg.sender.id] = EvictingList(20)
            if msg.group.id not in times:
                times[msg.group.id] = {}
            if msg.sender.id not in avg_samples:
                avg_samples[msg.sender.id] = EvictingList(7)

            if msg.sender.id not in times[msg.group.id]:
                times[msg.group.id][msg.sender.id] = time.time()
                return

            e_list: EvictingList = TIME_SAMPLES[msg.group.id][msg.sender.id]
            e_list.add(time.time() - times[msg.group.id][msg.sender.id])
            times[msg.group.id][msg.sender.id] = time.time()

            if e_list.size() >= e_list.get_max_size():
                delta_time = 0.0
                for i in e_list.get_list():
                    delta_time += i
                avg_time = delta_time / e_list.get_max_size()
                e: EvictingList = avg_samples[msg.sender.id]
                e.add(avg_time)

                if mathUtils.stdev(e.get_list()) < 0.05:
                    event.get_message().mute(86400)
