import time


class BiliUtils:
    def __init__(self, cache_time=60):
        self.cache_time = cache_time
        self.cache = {}

    def get_video(self, bvid):
        if bvid is None:
            raise TypeError()

        if bvid in self.cache and self.cache["time"] <= time.time() - self.cache_time:
            return self.cache["raw"]

        pass
