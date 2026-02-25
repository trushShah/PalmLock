import cv2
import mediapipe as mp
import time
import ctypes
import threading
import tkinter as tk
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import pyautogui

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05

from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL

# ===============================
# STATUS PANEL
# ===============================

class StatusPanel:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.config(bg="black")
        self.root.attributes("-transparentcolor", "black")
        self.root.geometry("130x40+0+0")

        self.canvas = tk.Canvas(
            self.root,
            width=130,
            height=40,
            bg="black",
            highlightthickness=0
        )
        self.canvas.pack()

        self.state = "MONITORING"
        self.update_ui()

    def update_state(self, new_state):
        self.state = new_state
        self.update_ui()

    def draw_dot(self, x, color, active):
        if active:
            self.canvas.create_oval(x-12, 10, x+12, 34, fill=color, outline="")
        else:
            self.canvas.create_oval(x-12, 10, x+12, 34, fill="#2a2a2a", outline="")

    def update_ui(self):
        self.canvas.delete("all")
        positions = [30, 65, 100]
        self.draw_dot(positions[0], "#ff3b3b", self.state == "MONITORING")
        self.draw_dot(positions[1], "#ffd000", self.state == "HAND")
        self.draw_dot(positions[2], "#00ff88", self.state == "STABLE")
        self.root.update()

    def close(self):
        if self.root:
            self.root.destroy()


# ===============================
# GESTURE ENGINE
# ===============================

class GestureEngine:
    def __init__(self):
        self.running = False
        self.thread = None
        self.panel = None
        self.cooldown_until = 0

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_,
            CLSCTX_ALL,
            None
        )
        self.volume = cast(interface, POINTER(IAudioEndpointVolume))

    def start(self):
        if self.thread and self.thread.is_alive():
            return

        self.running = True
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    # ---------------------------
    # Gesture Helpers
    # ---------------------------

    def count_fingers(self, landmarks):
        tips = [8, 12, 16, 20]
        count = 0
        for tip in tips:
            if landmarks.landmark[tip].y < landmarks.landmark[tip - 2].y:
                count += 1
        return count

    def palm_orientation_front(self, landmarks):
        # Front-facing palm detection
        return landmarks.landmark[0].z < landmarks.landmark[9].z

    def direction_up(self, landmarks):
        wrist_y = landmarks.landmark[0].y
        tips = [8, 12, 16, 20]

        active_tips = []
        for tip in tips:
            if landmarks.landmark[tip].y < landmarks.landmark[tip - 2].y:
                active_tips.append(tip)

        if not active_tips:
            return False

        avg_tip_y = sum(landmarks.landmark[t].y for t in active_tips) / len(active_tips)
        return avg_tip_y < wrist_y

    # ---------------------------
    # Actions
    # ---------------------------

    def action_show_desktop(self):
        pyautogui.hotkey('win', 'd')

    def action_screenshot(self):
        pyautogui.hotkey('win', 'shift', 's')

    # def action_close_window(self):
    #     pyautogui.keyDown('alt')
    #     time.sleep(0.05)
    #     pyautogui.press('f4')
    #     time.sleep(0.05)
    #     pyautogui.keyUp('alt')

    def action_volume_up_half(self):
        current = self.volume.GetMasterVolumeLevelScalar()
        current_percent = current * 100
        new_percent = min(100, current_percent + (current_percent / 2))
        self.volume.SetMasterVolumeLevelScalar(new_percent / 100, None)

    def action_volume_down_half(self):
        current = self.volume.GetMasterVolumeLevelScalar()
        current_percent = current * 100
        new_percent = current_percent / 2
        self.volume.SetMasterVolumeLevelScalar(new_percent / 100, None)

    # ---------------------------
    # Main Loop
    # ---------------------------

    def run(self):
        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

        cap = cv2.VideoCapture(0)
        self.panel = StatusPanel()

        stable_start = None
        STABLE_TIME = 1.0

        while self.running:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)

            now = time.time()

            if now < self.cooldown_until:
                self.panel.update_state("MONITORING")
                continue

            if result.multi_hand_landmarks:
                for hand_landmarks in result.multi_hand_landmarks:

                    fingers = self.count_fingers(hand_landmarks)
                    is_front = self.palm_orientation_front(hand_landmarks)
                    is_up = self.direction_up(hand_landmarks)

                    self.panel.update_state("HAND")

                    if stable_start is None:
                        stable_start = now
                    elif now - stable_start >= STABLE_TIME:

                        self.panel.update_state("STABLE")
                        time.sleep(0.3)

                        # ==========================
                        # GESTURE MAPPING
                        # ==========================

                        # Palm (strict: 4 fingers + front)
                        if fingers == 4 and is_front:
                            ctypes.windll.user32.LockWorkStation()
                            self.running = False
                            # cap.release()
                            # self.panel.close()
                            return

                        # Fist (front)
                        elif fingers == 0 and is_front:
                            self.action_show_desktop()

                        # Two fingers (back)
                        elif fingers == 2 and not is_front:
                            if is_up:
                                self.action_volume_up_half()
                            else:
                                self.action_volume_down_half()

                        # Three fingers (back)
                        elif fingers == 3 and not is_front:
                            if is_up:
                                self.action_screenshot()

                        # elif fingers == 1 and not is_front:
                        #     self.action_close_window()

                        self.cooldown_until = time.time() + 5
                        stable_start = None

            else:
                stable_start = None
                self.panel.update_state("MONITORING")

        cap.release()
        if self.panel:
            self.panel.close()


# ===============================
# TRAY
# ===============================

engine = GestureEngine()

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