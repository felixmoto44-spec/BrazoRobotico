"""
Servidor Flask + WebSocket — UNO Q (Qualcomm Linux)
Recibe landmarks → envía comandos al STM32U585 vía SOCAT TCP:7500.

Ruta: Flask → TCP:7500 → SOCAT → USB CDC ACM → STM32 Serial → Serial1 → Mega
"""

import json
import time
import math
from flask import Flask, send_from_directory
from flask_sock import Sock

app = Flask(__name__)
sock = Sock(app)

SERIAL_HOST = "127.0.0.1"
SERIAL_PORT = 7500

ANGLE_THRESHOLD = {"thumb": 12, "finger": 8}
MAX_CHANGE = 5
SENSITIVITY = 0.85
STABILITY_FRAMES = 3

FINGER_CALIB = {
    "thumb": {"open": 40, "closed": 160},
    "index": {"open": 0,  "closed": 170},
    "middle": {"open": 0, "closed": 170},
    "ring": {"open": 0, "closed": 170},
    "pinky": {"open": 0, "closed": 170},
}

last_angles = [90, 90, 90, 90, 90]
stable_count = [0, 0, 0, 0, 0]
debug_frame = 0


def angle_between_3d(v1, v2):
    dot = v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]
    m1 = math.sqrt(v1[0]**2 + v1[1]**2 + v1[2]**2)
    m2 = math.sqrt(v2[0]**2 + v2[1]**2 + v2[2]**2)
    if m1 < 1e-9 or m2 < 1e-9:
        return 180.0
    cos_val = max(-1.0, min(1.0, dot / (m1 * m2)))
    return math.degrees(math.acos(cos_val))


def joint_angle_3d(lm, a, b, c):
    v1 = (lm[c]["x"] - lm[b]["x"], lm[c]["y"] - lm[b]["y"], lm[c]["z"] - lm[b]["z"])
    v2 = (lm[a]["x"] - lm[b]["x"], lm[a]["y"] - lm[b]["y"], lm[a]["z"] - lm[b]["z"])
    return angle_between_3d(v1, v2)


def landmarks_to_angles(landmarks):
    global debug_frame
    if not landmarks or len(landmarks) < 21:
        return [90, 90, 90, 90, 90]

    debug_frame += 1
    lm = landmarks
    angles = []
    names = ["THB", "IDX", "MID", "RNG", "PNK"]

    # Thumb: angle between wrist→index(5) and wrist→thumb_tip(4)
    try:
        abduction = joint_angle_3d(lm, 5, 0, 4)
        thumb_raw = max(30, min(170, (90 - abduction) * 2.0 + 30))
        thumb = lerp(thumb_raw, FINGER_CALIB["thumb"]["open"], FINGER_CALIB["thumb"]["closed"])
    except Exception:
        thumb = 90
    angles.append(thumb)

    # 4 fingers: PIP joint angle in 3D
    fingers = [
        (5, 6, 8, "index"),
        (9, 10, 12, "middle"),
        (13, 14, 16, "ring"),
        (17, 18, 20, "pinky"),
    ]

    for i, (mcp, pip, tip, name) in enumerate(fingers):
        try:
            flexion = joint_angle_3d(lm, mcp, pip, tip)
            raw = 180 - flexion
            raw = raw * SENSITIVITY
            calib = FINGER_CALIB[name]
            servo = lerp(raw, calib["open"], calib["closed"])
        except Exception:
            servo = 90
        angles.append(servo)

    return angles


def lerp(value, out_min, out_max):
    in_min, in_max = 0, 180
    value = max(in_min, min(in_max, value))
    return out_min + (out_max - out_min) * (value - in_min) / (in_max - in_min)


def open_uart():
    import socket
    for attempt in range(10):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.0)
            s.connect((SERIAL_HOST, SERIAL_PORT))
            return s
        except Exception:
            time.sleep(0.5)
    return None


def send_command(sock, idx, angle):
    global last_angles, stable_count
    angle = max(0, min(180, int(angle)))
    prev = last_angles[idx]

    thresh = ANGLE_THRESHOLD["thumb"] if idx == 0 else ANGLE_THRESHOLD["finger"]
    diff = abs(angle - prev)

    if diff < thresh:
        stable_count[idx] = 0
        return

    stable_count[idx] += 1
    if stable_count[idx] < STABILITY_FRAMES:
        return

    clamped = prev + max(-MAX_CHANGE, min(MAX_CHANGE, angle - prev))
    clamped = max(0, min(180, int(clamped)))
    cmd = f"M{idx} {clamped}\n"
    try:
        sock.sendall(cmd.encode())
        last_angles[idx] = clamped
        stable_count[idx] = 0
        if debug_frame % 10 == 0:
            print(f"  M{idx}: {clamped}°")
    except Exception:
        pass


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@sock.route("/ws")
def ws_handler(ws):
    global last_angles, stable_count
    last_angles = [90, 90, 90, 90, 90]
    stable_count = [0, 0, 0, 0, 0]
    print("Cliente WebSocket conectado")

    sock = open_uart()
    if not sock:
        print("ERROR: No se pudo conectar al STM32")

    try:
        while True:
            msg = ws.receive()
            if msg is None:
                break

            data = json.loads(msg)
            landmarks = data.get("landmarks", [])
            client_ts = data.get("timestamp", time.time())
            angles = landmarks_to_angles(landmarks)

            for i in range(5):
                if sock:
                    send_command(sock, i, angles[i])

            last_angles = angles.copy()
            ws.send(json.dumps({"angles": angles, "timestamp": client_ts}))

    except Exception as e:
        print(f"Error WebSocket: {e}")

    if sock:
        sock.close()
    print("Cliente WebSocket desconectado")


if __name__ == "__main__":
    print("Arrancando servidor Flask + WebSocket HTTPS en :3000")
    app.run(host="0.0.0.0", port=3000, ssl_context=("cert.pem", "key.pem"), debug=False)
