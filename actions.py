import pyautogui
import ctypes
import time

from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL


pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05


class Actions:
    def __init__(self):
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_,
            CLSCTX_ALL,
            None
        )
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))

    def lock(self):
        ctypes.windll.user32.LockWorkStation()

    def show_desktop(self):
        pyautogui.hotkey('win', 'd')

    def screenshot(self):
        pyautogui.hotkey('win', 'shift', 's')

    def volume_up_half(self):
        current = self.volume.GetMasterVolumeLevelScalar()
        current_percent = current * 100
        new_percent = min(100, current_percent + (current_percent / 2))
        self.volume.SetMasterVolumeLevelScalar(new_percent / 100, None)

    def volume_down_half(self):
        current = self.volume.GetMasterVolumeLevelScalar()
        current_percent = current * 100
        new_percent = current_percent / 2
        self.volume.SetMasterVolumeLevelScalar(new_percent / 100, None)