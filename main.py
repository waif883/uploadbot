import os
import shutil
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
    UPLOAD_WAIT_HOURS = 0.001388888889
else:
    # CHECK_FILE_DURATION_SECONDS = 5*60
    ARCHIVE_DIRECTORY = os.path.join("W:", os.sep, "OneDrive - The Real StepChild Radio Of Cincinnati One", "New Recording")
    CHECK_FILE_DURATION_SECONDS = 5*60
    UPLOAD_WAIT_HOURS = 1
    
    
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
    os.remove(log_path)
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
        
    last_archive_directory_content = glob.glob(os.path.join(ARCHIVE_DIRECTORY, "*"))
    audio_file_upload_queue = list()
    
    while True:
        
        current_archive_directory_content = glob.glob(os.path.join(ARCHIVE_DIRECTORY, "*"))
        
        new_audio_files = set(current_archive_directory_content) - set(last_archive_directory_content)
        new_audio_files = [file for file in new_audio_files if os.path.splitext(file)[-1].lower() == '.mp3']
        
        if new_audio_files:
            logging.info(f"Found new files: \n{pprint.pformat(new_audio_files)}")
        
        audio_file_upload_queue += [{
            "file": file,
            "time": datetime.datetime.now()
        } for file in new_audio_files]
        
        for i, item in enumerate(audio_file_upload_queue):
            file = item["file"]
            found_at_time = item["time"]
            archive_datetime = waif.parse_archive_filename(file)
            filesize_mb = utils.byte2megabyte(os.path.getsize(file))
            program = match_archive_to_program(archive_datetime, programs)
            
            if program:
                hours_waited = utils.seconds2hours((datetime.datetime.now() - found_at_time).total_seconds())
                if (hours_waited > UPLOAD_WAIT_HOURS):
                    logging.info(f"{hours_waited} hours have elapsed, ready to upload {file}.")
                    try:
                        waif.upload_to_mixcloud(program, file, archive_datetime, secrets)
                    except:
                        logging.error(f"Could not upload {file} to mixcloud.")
                    audio_file_upload_queue[i] = None
                else:
                    logging.info(f"{hours_waited} hours have elapsed, not ready to uplad {file}.")
            else:
                logging.info(f"File \"{file}\" does not match a program. It will not be uploaded.")
                audio_file_upload_queue[i] = None
        
        # consolidate queue
        audio_file_upload_queue = [file for file in audio_file_upload_queue if file is not None]
                
        last_archive_directory_content = current_archive_directory_content
        time.sleep(CHECK_FILE_DURATION_SECONDS)


if __name__ == "__main__":
    main()
