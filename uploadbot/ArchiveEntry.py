import datetime
import pathlib

from RadioProgram import RadioProgram

class ArchiveEntry:
    
    file: pathlib.Path
    """Path to archive MP3 file."""
    
    creation_time: datetime.datetime
    """Time reported in archive file name."""
    
    discovery_time: datetime.datetime
    """Time when archive was found."""
    
    program: RadioProgram
    """Radio program associated with archive file"""
    
    def __init__(self, 
                 file: pathlib.Path, 
                 creation_time: datetime.datetime, 
                 discovery_time: datetime.datetime, 
                 program: RadioProgram
    ):
        self.file = file
        self.creation_time = creation_time
        self.discovery_time = discovery_time
        self.program = program