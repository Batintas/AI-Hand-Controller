AI Hand Controller V1.0 🤖🖐️
A Computer Vision-based Human-Machine Interface (HMI) designed for touchless computer navigation. This project focuses on solving common sensor occlusion issues using state machine logic and integrating hardware-inspired safety mechanisms into a software environment.

🚀 Key Engineering Features
Real-Time Skeletal Tracking: Utilizes OpenCV and MediaPipe with dynamic smoothing algorithms to eliminate cursor jitter.

Sensor Override Logic: Incorporates a state machine that forces logic states when fingers overlap (e.g., during pinch-and-drag operations), preventing tracking loss.

Deadman's Switch (Hot Corner): A failsafe mechanism. Moving the index finger to the top-left corner initiates a locking sequence. Once activated, the system goes into "SYSTEM SLEEP" mode, immediately executing a forced mouse-release (mouseUp) to prevent the OS cursor from sticking.

Dynamic HUD: Real-time on-screen display logging the system state (DRAGGING, READY TO CLICK, STANDBY) and FPS for performance monitoring.

🛠️ Requirements & Installation
To run this project from the source code, you need Python installed on your system along with the following libraries:

pip install opencv-python mediapipe cvzone pyautogui numpy

Note: Ensure the hand_landmarker.task model file is in the same directory as the script before running.

🎯 Usage
If you want to test the application without setting up a Python environment, you can download the standalone .exe version from the Releases section on the right sidebar.
