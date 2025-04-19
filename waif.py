import os
import re
import datetime
import logging
import requests
import csv
import time
import datetime 

import airtable

import utils
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

def get_programs(secrets):
    # load programs
    # programs = list()
    # reader = csv.DictReader(open(PROGRAM_CSV_FILE))
    # for row in reader:
    #     programs.append(
    #         RadioProgram(row)
    #     )
    programs = list()
    at = airtable.Airtable(secrets["AIRTABLE"]["BASE_ID"], secrets["AIRTABLE"]["ACCESS_TOKEN"])
    r = at.get("Programs")
    r = r["records"]
    for item in r:
        item = item["fields"]
        program = RadioProgram(name=item["Show"], 
                            start_day_str=item["Start Day"],
                            start_hour=item["Start Time (24hr)"],
                            end_day_str=item["End Day"],
                            end_hour=item["End Time (24hr)"],
                            description=item["Description"],
                            promo=item["Promo Text"])
        programs.append(program)
    return programs

def match_archive_to_program(archive_datetime: datetime.datetime, secrets: dict):
    
    programs = get_programs(secrets)
    
    # find program 
    program = None
    program = None
    archive_day = utils.WEEKDAYS[archive_datetime.weekday()]
    archive_hour = archive_datetime.hour
    selected_program = None
    for program in programs:

        day_match = (archive_day == program.start_day_str) or (archive_day == program.end_day_str)
        time_match = archive_hour >= program.start_hour and archive_hour < program.end_hour
        
        if day_match and time_match:
            selected_program = program
            if archive_hour == (program.end_hour):
                is_last_hour = True
            break
    return selected_program

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

    start_p = "AM" if archive_datetime.hour < 12 else "PM"
    end_p = "AM" if archive_end_datetime.hour < 12 else "PM"
    data = {
        'name': f"{program.name} {archive_datetime.month}/{archive_datetime.day}/{archive_datetime.year} {archive_datetime.hour}{start_p}-{archive_end_datetime.hour}{end_p}", 
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
    
    url = f"https://api.mixcloud.com/upload/?access_token={secrets['MIXCLOUD']['ACCESS_TOKEN']}"

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