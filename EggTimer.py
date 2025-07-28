import time
import datetime

class EggTimer:
    def __init__(self, duration_s: float):
        self.duration_s: float= duration_s
        self.start_time: datetime.datetime=None
        self.last_checked_time: datetime.datetime=None
        self.elapsed_s: float=0
        
    def start(self):
        self.start_time = datetime.datetime.now()
        
        
    def has_elapsed(self) -> bool:
        self.last_checked_time = datetime.datetime.now()
        
        self.elapsed_s = (self.last_checked_time - self.start_time).total_seconds()
        if self.elapsed_s > self.duration_s:
            return True
        else:
            return False