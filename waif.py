import os
import re
import datetime
import logging
import requests
import time
import datetime 

from utils import WEEKDAYS
from RadioProgram import RadioProgram

def parse_archive_filename(file):
    if os.sep in file:
        file = os.path.basename(file)
    parts = re.split('-|_|\s|;', file)
    archive_datetime = datetime.datetime(year=int(parts[2]), 
                            month=int(parts[0]), 
                            day=int(parts[1]),
                            hour=int(parts[5])
                        )
    # if time.localtime().tm_isdst > 0:
    #     archive_date = archive_date + datetime.timedelta(hours=1, minutes=0)

    return archive_datetime

def upload_to_mixcloud(program: RadioProgram, 
                       file: str, 
                       archive_datetime: datetime.datetime,
                       secrets: dict):
    logging.info(f"Preparing to upload {program.name}")

    # upload temp file to Mixcloud
    archive_end_datetime = archive_datetime + datetime.timedelta(hours=1, minutes=0)
    description = (f"{program.start_day_str} from {archive_datetime.strftime('%A, %B %d, %Y %I:%M %p')} to {archive_end_datetime.strftime('%A, %B %d, %Y %I:%M %p')}. "
                    f"\n"
                    f"{program.promo}")
    description = description.replace(u'\xa0', u' ')
    description = description.replace('\ufffd', '')

    tags = program.description.split(",")

    start_12hr = archive_datetime.strftime("%I%p")
    end_12hr = archive_end_datetime.strftime("%I%p")
    data = {
        'name': f"{program.name} {archive_datetime.month}/{archive_datetime.day}/{archive_datetime.year} {start_12hr}-{end_12hr}", 
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
        f'tags-{n+1}-tag': f"WAIF: {program.name}"
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