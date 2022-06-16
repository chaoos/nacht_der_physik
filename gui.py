#!/usr/bin/env python3

import argparse
import os
import json
import time
import eel

@eel.expose
def get_json(file, delay = 0.1):
    while(True):
        try:
            with open(file, 'r') as f:
                try:
                    return json.load(f)
                except:
                    pass
        except:
            pass

        time.sleep(delay)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = 'GUI')
    args = parser.parse_args()

    eel.init("web")  
    eel.start("index.html")