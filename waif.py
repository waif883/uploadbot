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
    for n, item in enumerate(r):
        item = item["fields"]
        if all(key in item for key in ["Show", "Start Day", "Start Time (24hr)", "End Day", "End Time (24hr)", "Description", "Promo Text"]):
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
    archive_day = utils.WEEKDAYS[archive_datetime.weekday()]
    archive_hour = archive_datetime.hour
    selected_program = None
    for program in programs:

        end_hour = program.end_hour
        if end_hour < program.start_hour:
            end_hour += 24

        day_match = (archive_day == program.start_day_str) or (archive_day == program.end_day_str)
        time_match = archive_hour >= program.start_hour and archive_hour < end_hour
        
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
    description = (f"{archive_datetime.strftime('%A, %B %d, %Y %I:%M %p')} to {archive_end_datetime.strftime('%A, %B %d, %Y %I:%M %p')}. "
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