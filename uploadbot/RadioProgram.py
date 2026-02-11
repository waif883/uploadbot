import pprint
import datetime

import utils

class RadioProgram:
    name: str
    start_day_str: str
    start_day_int: int
    start_hour: int
    end_day_str: int
    end_day_int: int
    end_hour: int
    description: str
    num_hours: int
    promo: str
    def __init__(self, 
                 name: str, 
                 start_day_str: str,
                 start_hour: int,
                 end_day_str: str,
                 end_hour: int,
                 description: str,
                 promo: str):
        """Constructor from CSV Row
        """
        self.name = name
        self.start_day_str = start_day_str
        self.start_day_int = self._get_day_int(self.start_day_str)
        self.start_hour = int(start_hour.split(':')[0])
        self.end_day_str = end_day_str.strip()
        self.end_day_int = self._get_day_int(self.end_day_str)
        self.end_hour = int(end_hour.split(':')[0])
        self.promo = promo
        self.description = description
        self._get_num_hours()
        
    def _get_day_int(self, day: str):
        day = day.strip()
        return next(iter([i for i, day_str in utils.WEEKDAYS.items() if day_str == day]), None)
    
    def _get_num_hours(self):
        start_datetime = utils.find_first_dow(2025, 1, self.start_day_int)
        start_datetime = start_datetime.replace(hour=self.start_hour)
        end_datetime = utils.find_first_dow(2025, 1, self.end_day_int)
        end_datetime = end_datetime.replace(hour=self.end_hour)
        if end_datetime < start_datetime:
            end_datetime += datetime.timedelta(days=7)
        duration_seconds = (end_datetime - start_datetime).total_seconds()
        self.num_hours = utils.seconds2hours(duration_seconds)
    
    def __str__(self):
        return pprint.pformat(vars(self), indent=4)

    def __repr__(self):
        return pprint.pformat(vars(self), indent=4)