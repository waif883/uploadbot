import argparse
import csv
import datetime
import glob
import json
import logging
import os
import pathlib
import pprint
import pickle
import shutil
import soundfile as sf
import time

from EggTimer import EggTimer
from RadioProgram import RadioProgram
import utils
import waif 

def get_programs(programs: list, secrets: dict, config: dict):
    """Try to get programs from airtable, but if this fails load from disk.

    Args:
        programs (list): List of RadioProgram elements.
        secrets (dict): Secrets for airtable and mixcloud.
        config (dict): Configuration for Upload Bot.

    Returns:
        list: List of programs.
    """
    try:
        programs = waif.get_programs_from_airtable(secrets)
        with open(config["PROGRAMS_TABLE_FILE"], 'wb') as f:
            pickle.dump(programs, f, pickle.HIGHEST_PROTOCOL)
    except:
        logging.exception('Could not read from airtable. Trying to load from disk')
        try:
            with open(config["PROGRAMS_TABLE_FILE"], 'rb') as f:
                programs = pickle.load(f)
        except:
            logging.exception('Could not read from disk. Damn. You are on your own, cowboy.')
    return programs

def start_upload_server(
    config: dict, 
    secrets: dict
):
    """Launch Mixcloud Upload Bot server.

    Args:
        secrets (dict): Secrets for airtable and mixcloud.
        config (dict): Configuration for Upload Bot.
    """
    
    # log start
    logging.info(f"W.A.I.F. MixCloud Upload Server booted.")
        
    # get paths from config
    ARCHIVE_DIRECTORY = pathlib.Path(config["ARCHIVE_DIRECTORY"])
        
    # read files on disk
    last_archive_directory_content = ARCHIVE_DIRECTORY.glob("*")
    audio_file_upload_queue = list()
    
    # start the program timer
    program_timer = EggTimer(config["PROGRAM_TIMER_DURATION_SECONDS"])
    program_timer.start()
    
    # get programs from airtable and store
    programs = waif.get_programs_from_airtable(secrets)
    with open(config["PROGRAMS_TABLE_FILE"], 'wb') as f:
        pickle.dump(programs, f, pickle.HIGHEST_PROTOCOL)
    
    # observation loop
    while True:
        
        # get program updates when timer elapses
        if program_timer.has_elapsed():
            get_programs(programs, secrets, config)
            program_timer.start()
        
        # check for new files
        current_archive_directory_content = ARCHIVE_DIRECTORY.glob('*')
        new_audio_files = set(current_archive_directory_content) - set(last_archive_directory_content)
        new_audio_files = [file for file in new_audio_files if os.path.splitext(file)[-1].lower() == '.mp3']
        
        if new_audio_files:
            logging.info(f"Found new files: \n{pprint.pformat(new_audio_files)}")
        
        # add new files to the upload queue
        audio_file_upload_queue += [{
            "file": file,
            "time": datetime.datetime.now()
        } for file in new_audio_files]
        
        # for each item in the queue match to a program and upload to mixcloud
        for i, item in enumerate(audio_file_upload_queue):
            file = item["file"]
            found_at_time = item["time"]
            archive_datetime = waif.parse_archive_filename(file)
            program = waif.match_archive_to_program(archive_datetime, secrets, programs)
            
            if program:
                hours_waited = utils.seconds2hours((datetime.datetime.now() - found_at_time).total_seconds())
                if (hours_waited > config["UPLOAD_WAIT_HOURS"]):
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
        
        # wait to check for a new upload
        time.sleep(config["CHECK_FILE_DURATION_SECONDS"])


if __name__ == "__main__":
    
    # set up logging
    log_path = "log"
    if os.path.exists(log_path):
        os.remove(log_path)
    logging.basicConfig(level=logging.INFO, 
                    format="%(asctime)s [%(levelname)s]: %(name)s: %(message)s", 
                    handlers=[
                        logging.FileHandler(log_path),
                        logging.StreamHandler()
                    ])

    # parse command line arguments
    parser = argparse.ArgumentParser(description='WAIF Mixcloud Upload Bot')
    parser.add_argument('-s','--secrets', help='JSON file with secrets for Mixcloud and Airtable.', required=True)
    parser.add_argument('-c','--config', help='JSON file with program configurations.', required=True)
    args = vars(parser.parse_args())
    
    # load files from memory
    with open(args.secrets, 'r'):
        secrets = json.load(args.secrets)
    with open(args.config, 'r'):
        config = json.load(args.config)
    
    # start server
    start_upload_server(
        secrets=secrets,
        config=config
    )
