import os
import shutil
import threading
import time

from newmain import main

if __name__ == "__main__":
    # clean up
    shutil.rmtree("example")
    os.mkdir("example")
    
    # start thread
    t = threading.Thread(target=main)
    t.start()
    
    # wait and copy file
    time.sleep(3)
    shutil.copyfile(os.path.join("tmp", "03-30-2025; TIME 11-03.mp3"), os.path.join("example", "03-30-2025; TIME 11-03.mp3"))