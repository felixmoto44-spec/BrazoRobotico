#!/usr/bin/env python3
"""
Servidor v2 — Procesamiento en UNO Q
Recibe frames JPEG por WebSocket → MediaPipe → IK → servos.
"""

import base64
import json
import time
import math

import cv2
import mediapipe as mp
import numpy as np
import socket
from flask import Flask, send_from_directory
from flask_sock import Sock

app = Flask(__name__)
sock = Sock(app)

# MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)

# Config
SERIAL_HOST = "127.0.0.1"
SERIAL_PORT = 7500

last_angles = [90, 90, 90, 90, 90]
ANGLE_THRESHOLD = {"thumb": 12, "finger": 8}
MAX_CHANGE = 5
SENSITIVITY = 0.85

FINGER_CALIB = {
    "thumb": {"open": 40, "closed": 160},
    "index": {"open": 0, "closed": 170},
    "middle": {"open": 0, "closed": 170},
    "ring": {"open": 0, "closed": 170},
    "pinky": {"open": 0, "closed": 170},
}


def angle_between_3d(v1, v2):
    dot = v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]
    m1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2 + v1[2] ** 2)
    m2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2 + v2[2] ** 2)
    if m1 < 1e-9 or m2 < 1e-9:
        return 180.0
    return math.degrees(math.acos(max(-1, min(1, dot / (m1 * m2)))))


def joint_angle_3d(lm, a, b, c):
    return angle_between_3d(
        (lm[c]["x"] - lm[b]["x"], lm[c]["y"] - lm[b]["y"], lm[c]["z"] - lm[b]["z"]),
        (lm[a]["x"] - lm[b]["x"], lm[a]["y"] - lm[b]["y"], lm[a]["z"] - lm[b]["z"]),
    )


def lerp(value, out_min, out_max):
    value = max(0, min(180, value))
    return out_min + (out_max - out_min) * value / 180


def frame_to_landmarks(jpeg_bytes):
    """Convierte un frame JPEG bytes → landmarks de MediaPipe."""
    arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return None
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)
    if not result.multi_hand_landmarks:
        return None
    lm = result.multi_hand_landmarks[0]
    return [{"x": p.x, "y": p.y, "z": p.z} for p in lm.landmark]


def landmarks_to_angles(landmarks):
    if not landmarks or len(landmarks) < 21:
        return [90, 90, 90, 90, 90]
    lm = landmarks
    angles = []
    try:
        abduction = joint_angle_3d(lm, 5, 0, 4)
        thumb_raw = max(30, min(170, (90 - abduction) * 2.0 + 30))
        thumb = lerp(thumb_raw, FINGER_CALIB["thumb"]["open"], FINGER_CALIB["thumb"]["closed"])
    except Exception:
        thumb = 90
    angles.append(thumb)
    for mcp, pip, tip in [(5, 6, 8), (9, 10, 12), (13, 14, 16), (17, 18, 20)]:
        try:
            flexion = joint_angle_3d(lm, mcp, pip, tip)
            raw = (180 - flexion) * SENSITIVITY
            calib = FINGER_CALIB.get(
                ["index", "middle", "ring", "pinky"][
                    [(5, 6, 8), (9, 10, 12), (13, 14, 16), (17, 18, 20)].index(
                        (mcp, pip, tip)
                    )
                ],
                {"open": 0, "closed": 170},
            )
            servo = lerp(raw, calib["open"], calib["closed"])
        except Exception:
            servo = 90
        angles.append(servo)
    return angles


def connect_serial():
    for _ in range(10):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((SERIAL_HOST, SERIAL_PORT))
            return s
        except Exception:
            time.sleep(0.5)
    return None


def send_servo(sock, idx, angle):
    global last_angles
    angle = max(0, min(180, int(angle)))
    prev = last_angles[idx]
    thresh = ANGLE_THRESHOLD["thumb"] if idx == 0 else ANGLE_THRESHOLD["finger"]
    diff = abs(angle - prev)
    if diff < thresh:
        return
    clamped = prev + max(-MAX_CHANGE, min(MAX_CHANGE, angle - prev))
    clamped = max(0, min(180, int(clamped)))
    cmd = f"M{idx} {clamped}\n"
    try:
        sock.sendall(cmd.encode())
        last_angles[idx] = clamped
    except Exception:
        pass


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@sock.route("/ws")
def ws_handler(ws):
    global last_angles
    last_angles = [90, 90, 90, 90, 90]
    print("Cliente WebSocket conectado (v2 server-side)")
    ser = connect_serial()
    try:
        while True:
            msg = ws.receive()
            if msg is None:
                break
            data = json.loads(msg)
            frame_b64 = data.get("frame")
            if frame_b64:
                jpeg = base64.b64decode(frame_b64)
                landmarks = frame_to_landmarks(jpeg)
                angles = landmarks_to_angles(landmarks) if landmarks else [90] * 5
            else:
                angles = [90] * 5

            if ser:
                for i in range(5):
                    send_servo(ser, i, angles[i])

            ws.send(json.dumps({"angles": angles, "timestamp": data.get("timestamp", 0)}))
    except Exception as e:
        print(f"WebSocket error: {e}")
    if ser:
        ser.close()
    print("Cliente WebSocket desconectado")


if __name__ == "__main__":
    print("v2 Server — MediaPipe en UNO Q")
    app.run(host="0.0.0.0", port=3000, ssl_context=("cert.pem", "key.pem"), debug=False)
