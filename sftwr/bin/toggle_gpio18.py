#!/usr/bin/env python3

import subprocess
import time
import signal
import sys

GPIO = "18"
DELAY = 1.0  # seconds

running = True

def run_cmd(*args):
    subprocess.run(args, check=True)

def cleanup():
    # Return pin to input when exiting
    try:
        run_cmd("pinctrl", "set", GPIO, "ip")
    except Exception:
        pass

def handle_exit(signum, frame):
    global running
    running = False

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

try:
    # Set as output
    run_cmd("pinctrl", "set", GPIO, "op")

    state = 0
    while running:
        if state:
            run_cmd("pinctrl", "set", GPIO, "dh")  # drive high
            print(f"GPIO{GPIO} HIGH")
        else:
            run_cmd("pinctrl", "set", GPIO, "dl")  # drive low
            print(f"GPIO{GPIO} LOW")
        state = 1 - state
        time.sleep(DELAY)

finally:
    cleanup()
    print(f"GPIO{GPIO} returned to input")
