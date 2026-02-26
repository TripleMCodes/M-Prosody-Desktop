###This script is for development purposes

import os
import sys
import subprocess
from watchfiles import watch

APP_ENTRY = [sys.executable, "C:/Users/nkosikhona/LL DeskTop/mprosody/app.py"]  

def run():
    print("Watching for changes... (Ctrl+C to stop)")
    p = subprocess.Popen(APP_ENTRY)

    try:
        for changes in watch(".", watch_filter=lambda c: c.endswith((".py", ".qss", ".ui"))):
            print("Change detected, restarting:", changes)
            p.terminate()
            try:
                p.wait(timeout=2)
            except subprocess.TimeoutExpired:
                p.kill()
            p = subprocess.Popen(APP_ENTRY)
    finally:
        p.terminate()

if __name__ == "__main__":
    run()