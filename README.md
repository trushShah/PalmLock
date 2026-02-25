# PalmLock

PalmLock is a Windows background utility that enables gesture-based system control using your webcam.

## Features

- Palm (front) → Lock workstation
- Fist (front) → Show desktop
- 2 fingers (back, up/down) → Volume control
- 3 fingers (back, up) → Screenshot
- System tray integration
- Auto-start on boot
- MediaPipe-powered real-time detection

## Architecture

- Modular Python structure
- MediaPipe for hand tracking
- PyAutoGUI for OS automation
- Pycaw for volume control
- PyInstaller packaging (onedir build recommended)

## Build

```bash
pyinstaller --name PalmLock --onedir --noconsole --collect-all mediapipe --hidden-import=pycaw --hidden-import=comtypes main.py