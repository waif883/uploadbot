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
    def __init__(self, row):
        """Constructor from CSV Row

        Args:
            row (_type_): row in the Shows.csv
        """
        self.name = row['Show']
        self.start_day_str = row['Start Day'].strip()
        self.start_day_int = self._get_day_int(self.start_day_str)
        self.start_hour = int(row['Start Time (24hr)'].split(':')[0])
        self.end_day_str = row['End Day'].strip()
        self.end_day_int = self._get_day_int(self.end_day_str)
        self.end_hour = int(row['End Time (24hr)'].split(':')[0])
        self.promo = row['Promo Text']
        self.description = row['Description']
        self._get_num_hours()
        
    def _get_day_int(self, day: str):
        return next(iter([i for i, day_str in utils.WEEKDAYS.items() if day_str == day]))
    
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