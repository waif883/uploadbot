import os
import shutil
import threading
import time

from main import main

if __name__ == "__main__":
    # clean up
    shutil.rmtree("example")
    os.mkdir("example")
    
    # start thread
    t = threading.Thread(target=main)
    t.start()
    
    # wait and copy file
    time.sleep(3)
    shutil.copyfile(os.path.join("tmp", "04-16-2025; TIME 17-00.mp3"), os.path.join("example", "04-16-2025; TIME 17-00.mp3"))