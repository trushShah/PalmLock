import os
import sys
import winreg

import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw

from engine import GestureEngine

engine = GestureEngine()


def add_to_startup():
    # This only works correctly when running as EXE
    if getattr(sys, 'frozen', False):
        exe_path = sys.executable
    else:
        # If running via python main.py, do nothing
        return

    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "PalmLock", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
    except Exception:
        pass


def create_image():
    image = Image.new("RGB", (64, 64), "black")
    dc = ImageDraw.Draw(image)
    dc.ellipse((16, 16, 48, 48), fill="white")
    return image


def enable(icon, item):
    engine.start()


def disable(icon, item):
    engine.stop()


def exit_app(icon, item):
    engine.stop()
    icon.stop()


def run_tray():
    add_to_startup()   # 👈 Auto-register on first run

    icon = pystray.Icon(
        "PalmLock",
        create_image(),
        "PalmLock",
        menu=pystray.Menu(
            item("Enable Gesture", enable),
            item("Disable Gesture", disable),
            item("Exit", exit_app)
        )
    )
    icon.run()