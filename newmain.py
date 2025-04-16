import os
import glob
import time
import json
import csv
import pprint
import logging
import datetime
import soundfile as sf

import utils
import waif 
from RadioProgram import RadioProgram

DEBUG = True

BUFFER_FILE = "threadbuffer.json"
PROGRAM_CSV_FILE = "Shows.csv"

if DEBUG:
    ARCHIVE_DIRECTORY = "example"
    CHECK_FILE_DURATION_SECONDS = 1
else:
    # CHECK_FILE_DURATION_SECONDS = 5*60
    CHECK_FILE_DURATION_SECONDS = 2
    ARCHIVE_DIRECTORY = os.path.join("W:", os.sep, "OneDrive - The Real StepChild Radio Of Cincinnati One", "New Recording")
    
ARCHIVE_DIRECTORY = "example"
PROGRAM_CSV_FILE = "Shows.csv"

def match_archive_to_program(archive_datetime: datetime.datetime, programs: list):
    # find program 
    program = None
    reader = csv.DictReader(open(PROGRAM_CSV_FILE))
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

def main():
    
    # set up logging
    log_path = "log"
    logging.basicConfig(level=logging.INFO, 
                    format="%(asctime)s [%(levelname)s]: %(name)s: %(message)s", 
                    handlers=[
                        logging.FileHandler(log_path),
                        logging.StreamHandler()
                    ])
    logging.info(f"W.A.I.F. MixCloud Upload Server booted.")
    
    # load secrets from memory
    with open("secrets.json", 'r') as f:
        secrets = json.load(f)
    
    # load programs
    programs = list()
    reader = csv.DictReader(open(PROGRAM_CSV_FILE))
    for row in reader:
        programs.append(
            RadioProgram(row)
        )
        
    old_files = glob.glob(os.path.join(ARCHIVE_DIRECTORY, "*"))
    file_queue = list()
    
    while True:
        new_files = glob.glob(os.path.join(ARCHIVE_DIRECTORY, "*"))
        
        found_files = set(new_files) - set(old_files)
        found_files = [file for file in found_files if os.path.splitext(file)[-1].lower() == '.mp3']
        
        if found_files:
            logging.info(f"Found new files: \n{pprint.pformat(found_files)}")
        
        file_queue += [{
            "file": file,
            "date": datetime.datetime.now()
        } for file in found_files]
        
        for i, item in enumerate(file_queue):
            file = item["file"]
            archive_datetime = waif.parse_archive_filename(file)
            filesize_mb = utils.byte2megabyte(os.path.getsize(file))
            program = match_archive_to_program(archive_datetime, programs)
            
            if program:
                if (filesize_mb > 55):
                    waif.upload_to_mixcloud(program, file, archive_datetime, secrets)
                    file_queue[i] = None
            else:
                logging.info(f"File \"{file}\" does not match a program. It will not be uploaded.")
                file_queue[i] = None
            
            hours_waited = utils.seconds2hours((datetime.datetime.now() - item["date"]).total_seconds())
            if hours_waited > 2:
                logging.info(f"File \"{file}\" has been on the queue for 2 hours but is not large enough to upload. Removing from queue.")
                file_queue[i] = None
        
        # consolidate queue
        file_queue = [file for file in file_queue if file is None]
                
        old_files = new_files
        time.sleep(CHECK_FILE_DURATION_SECONDS)


if __name__ == "__main__":
    main()