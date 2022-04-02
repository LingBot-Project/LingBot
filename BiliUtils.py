import time


class BiliUtils:
    def __init__(self, cache_time=60):
        self.cache_time = cache_time
        self.cache = {}

    def get_video(self, bvid):
        if bvid is None:
            raise TypeError()

        if bvid in self.cache and self.cache[bvid]["time"] <= time.time() - self.cache_time and self.cache[bvid]["type"] == "viedo":
            return self.cache[bvid]["raw"]

        pass

    def get_user(self, uid):
        if uid is None:
            raise TypeError()

        if uid in self.cache and self.cache[uid]["time"] <= time.time() - self.cache_time and self.cache[uid]["type"] == "user":
            return self.cache[uid]["raw"]

        pass
