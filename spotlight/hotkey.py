#!/Users/sebastianrafaellachica/codingprojects/seeleV1/myenv/bin/python3
from pynput import keyboard
import subprocess

def on_activate():
    subprocess.Popen(["myenv/bin/python3", "spotlight.py"])

while True:
    with keyboard.GlobalHotKeys({
            '<cmd>+<shift>+<space>': on_activate}) as h:
        h.join()
