import datetime
import json

WEEKDAYS = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday"
}

def seconds2hours(s):
    return s / 3600

def byte2megabyte(b):
    mb = b * 1e-6
    return mb

def find_first_dow(year, month, dow):
    d = datetime.datetime(year, int(month), 7)
    offset = -((d.weekday() - dow) % 7)
    return d + datetime.timedelta(offset)
