import os
import glob
import json
import re
import requests
import csv
import pprint
import logging
import tempfile
import threading
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import soundfile as sf
import numpy as np

WEEKDAYS = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday"
}

DEBUG = False
DAYLIGHT_SAVINGS = True

BUFFER_FILE = "threadbuffer.json"
PROGRAM_CSV_FILE = "Shows.csv"

if DEBUG:
    ARCHIVE_DIRECTORY = "example"
    CHECK_FILE_DURATION_SECONDS = 1
else:
    CHECK_FILE_DURATION_SECONDS = 5*60
    ARCHIVE_DIRECTORY = os.path.join("W:", os.sep, "OneDrive - The Real StepChild Radio Of Cincinnati One", "New Recording")


def get_post_time():
    now_gmt = datetime.now(ZoneInfo('Europe/London'))
    post_time = now_gmt + timedelta(minutes=30) 
    post_time_str = post_time.isoformat(timespec='seconds')
    post_time_str = post_time_str[:-6]
    return post_time_str
    
def get_archive_info(file):
    if os.sep in file:
        file = os.path.basename(file)
    parts = re.split('-|_|\s|;', file)
    archive_date = datetime(year=int(parts[2]), 
                            month=int(parts[0]), 
                            day=int(parts[1]),
                            hour=int(parts[5])
                        )
    if DAYLIGHT_SAVINGS:
        archive_date = archive_date + timedelta(hours=1, minutes=0)
    archive_day = WEEKDAYS[archive_date.weekday()]
    archive_hour = archive_date.hour
    return archive_date, archive_day, archive_hour

def add_file_to_queue(file):
    with open(BUFFER_FILE, 'r') as f:
        data = json.load(f)
    
    if "queue" not in data:
        data["queue"] = list()
    data["queue"].append(file)
    
    with open(BUFFER_FILE, 'w') as f:
        json.dump(data, f, indent=True)
        logging.info(f"Added {file} to queue.")  
        
def clear_queue():
    with open(BUFFER_FILE, 'r') as f:
        data = json.load(f)
        
    data["queue"] = []
    
    with open(BUFFER_FILE, 'w') as f:
        json.dump(data, f, indent=True)
        logging.info(f"Cleared queue.")  
    
def upload_file(file):

    # load secrets
    with open("secrets.json", 'r') as f:
        secrets = json.load(f)

    # parse archive file name
    archive_date, archive_day, archive_hour = get_archive_info(file)
        
    # find program 
    program = None
    reader = csv.DictReader(open(PROGRAM_CSV_FILE))
    is_last_hour = False
    program = None
    for row in reader:
        program_start_time = int(row['Start Time (24hr)'].split(':')[0])
        program_end_time = int(row['End Time (24hr)'].split(':')[0])
        day_match = archive_day == row['Start Day']
        time_match = archive_hour > program_start_time and archive_hour <= program_end_time
        if day_match and time_match:
            program = row
            if archive_hour == (program_end_time):
                is_last_hour = True
            break
            
    if program:
    

        logging.info(f"Preparing to upload {program['Show']}")

        # upload temp file to Mixcloud
        archive_start_date = archive_date - timedelta(hours=1, minutes=0)
        description = (f"{program['Start Day']} from {archive_start_date.strftime('%A, %B %d, %Y %I:%M %p')} to {archive_date.strftime('%A, %B %d, %Y %I:%M %p')}. "
                       f"\n"
                       f"{program['Promo Text']}")
        description = description.replace(u'\xa0', u' ')
        description = description.replace('\ufffd', '')

        tags = program['Description'].split(",")

        data = {
            'name': f"{program['Show']} {archive_start_date.strftime('%A, %B %d, %Y %I:%M %p')} , {archive_date.month}/{archive_date.day}/{archive_date.year}", 
            'description': description, 
            'publish_date': '',
            'user': 'WAIF883'
        }

        # add tags
        for n, tag in enumerate(tags):
            data = data | {
                f'tags-{n}-tag': tag
            }
        data |= {
            f'tags-{n+1}-tag': f"WAIF: {program['Show']}"
        }

        files = {
            'mp3': (file, open(file, 'rb'), 'audio/mpeg'),
        }
        
        url = f"https://api.mixcloud.com/upload/?access_token={secrets['ACCESS_TOKEN']}"

        logging.info(f"Posting to {url} with content:")
        logging.info(data)
        logging.info(files)

        r = requests.post(url, files=files, data=data)
        if r.status_code == 200:
            logging.info("Successful upload.")
            logging.info(r.json())
            logging.info(r.text)
        else:
            logging.error(f"Unsuccessful upload. Response code {r.status_code}.")
            logging.error(r.json())
            logging.error(r.text)
    
            
    else:
        logging.warning(f"Ooops, no show found for this file \"{file}\".")

def check_for_new_files():
    with open(BUFFER_FILE, 'r') as f:
        data = json.load(f)
    new_paths = glob.glob(os.path.join(data["path"], "*"))
    diff = set(new_paths) - set(data["paths"])
    with open(BUFFER_FILE, 'w') as f:
        data["paths"] = new_paths
        json.dump(data, f, indent=True)
    return diff

def repeat_function():
    new_files = check_for_new_files()
    if new_files:
        logging.info(f"Found new files: {new_files}")
        for file in new_files:
            if os.path.splitext(file)[-1].lower() == '.mp3':
                try:
                    upload_file(file)
                except:
                    logging.exception("Error while uploading:")
    else:
        logging.info("No new files found.")
    threading.Timer(CHECK_FILE_DURATION_SECONDS, repeat_function).start()

if __name__ == "__main__":
    
    now = datetime.now()
    log_path = "log"
    if DEBUG:
        log_path = f"{now.strftime('%Y%m%d%H%M%S')}_log"
    logging.basicConfig(level=logging.INFO, 
                        format="%(asctime)s [%(levelname)s]: %(name)s: %(message)s", 
                        handlers=[
                            logging.FileHandler(log_path),
                            logging.StreamHandler()
                        ])
    logging.info(f"W.A.I.F. MixCloud Upload Server booted.")
    
    archive_dir = ARCHIVE_DIRECTORY
    current_paths = glob.glob(os.path.join(archive_dir, "*"))
    
    # initialize buffer
    with open(BUFFER_FILE, 'w') as f:
        data = {
            "paths": current_paths,
            "path": archive_dir
        }
        json.dump(data, f, indent=True)
    
    repeat_function()