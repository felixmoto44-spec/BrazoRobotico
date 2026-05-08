#!/usr/bin/env python3
"""
Test v2 — Server-side processing
Envía frames JPEG de la webcam al UNO Q por WebSocket.
El UNO Q ejecuta MediaPipe y devuelve los ángulos.
"""

import asyncio
import base64
import json
import time
import cv2
import websockets

UNO_Q = "wss://192.168.31.12:3000/ws"
CAMERA = 0
WIDTH, HEIGHT = 320, 240
QUALITY = 50
FPS = 10


async def main():
    cap = cv2.VideoCapture(CAMERA)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

    print(f"Conectando a {UNO_Q} ...")
    async with websockets.connect(UNO_Q, ssl=None) as ws:
        print("Conectado. Enviando frames...")

        interval = 1.0 / FPS
        last = time.time()

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            now = time.time()
            if now - last < interval:
                await asyncio.sleep(0.001)
                continue
            last = now

            _, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, QUALITY])
            b64 = base64.b64encode(jpeg).decode()
            msg = json.dumps({"frame": b64, "timestamp": time.time() * 1000})
            t0 = time.time()
            await ws.send(msg)
            response = await ws.recv()
            rtt = (time.time() - t0) * 1000

            data = json.loads(response)
            angles = data.get("angles", [])
            if angles:
                a = [round(x) for x in angles]
                print(f"  RTT: {rtt:.0f}ms | Servos: {a}")

    cap.release()


if __name__ == "__main__":
    asyncio.run(main())
