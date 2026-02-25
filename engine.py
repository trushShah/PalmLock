import cv2
import mediapipe as mp
import time
import threading

from ui import StatusPanel
from actions import Actions
import config


class GestureEngine:
    def __init__(self):
        self.running = False
        self.thread = None
        self.panel = None
        self.cooldown_until = 0
        self.actions = Actions()

    def start(self):
        if self.thread and self.thread.is_alive():
            return

        self.running = True
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def count_fingers(self, landmarks):
        tips = [8, 12, 16, 20]
        count = 0
        for tip in tips:
            if landmarks.landmark[tip].y < landmarks.landmark[tip - 2].y:
                count += 1
        return count

    def palm_orientation_front(self, landmarks):
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

    def run(self):
        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=config.DETECTION_CONFIDENCE,
            min_tracking_confidence=config.TRACKING_CONFIDENCE
        )

        cap = cv2.VideoCapture(0)
        self.panel = StatusPanel()

        stable_start = None

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
                    elif now - stable_start >= config.STABLE_TIME:

                        self.panel.update_state("STABLE")
                        time.sleep(0.3)

                        if fingers == 4 and is_front:
                            self.actions.lock()
                            self.running = False
                            return

                        elif fingers == 0 and is_front:
                            self.actions.show_desktop()

                        elif fingers == 2 and not is_front:
                            if is_up:
                                self.actions.volume_up_half()
                            else:
                                self.actions.volume_down_half()

                        elif fingers == 3 and not is_front:
                            if is_up:
                                self.actions.screenshot()

                        self.cooldown_until = time.time() + config.COOLDOWN_TIME
                        stable_start = None

            else:
                stable_start = None
                self.panel.update_state("MONITORING")

        cap.release()
        if self.panel:
            self.panel.close()