
class EvictingList:
    def __init__(self, max_size):
        self._queue = []
        self.max_size = max_size
    
    def add(self, obj):
        self._queue.append(obj)
        if len(self._queue) > self.max_size:
            return self._queue.pop(0)
    
    def get(self, index):
        try:
            return self._queue[index]
        except Exception:
            return None
