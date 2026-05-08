# Brazo Robótico — Domain Context

Sistema de control de una mano robótica de 5 dedos mediante visión por computador.

## Language

**Tracking**:
Detección en tiempo real de la mano humana mediante MediaPipe (21 landmarks).
_Evitar_: detección, seguimiento

**3D Hand**:
Representación tridimensional de la mano con Three.js en el frontend.
_Evitar_: mano virtual, mano 3D, modelo 3D

**IK (Inverse Kinematics)**:
Conversión de 21 landmarks de MediaPipe a 5 ángulos de servo (0-180°).
_Evitar_: cinemática, mapeo

**Servo**:
Actuador MG996R que mueve un dedo. Recibe ángulo 0-180° vía PWM.
_Evitar_: motor, actuador

**Record**:
Grabación de frames (landmarks + ángulos) para reproducción posterior.
_Evitar_: grabar, grabación

**Replay**:
Reproducción de una grabación previamente almacenada.
_Evitar_: reproducir, reproducción

**Bridge**:
Sketch del STM32U585 que actúa como puente UART entre Qualcomm Linux y Arduino Mega.
_Evitar_: puente, pasarela

**Router**:
Servicio `arduino-router` que gestiona la comunicación entre Qualcomm y STM32 vía LPUART1.
_Evitar_: enrutador

**UNO Q**:
Arduino UNO Q (ABX00162) — placa con Qualcomm QRB2210 (Linux) + STM32U585 (MCU).
_Evitar_: placa, arduino

**Mega**:
Arduino Mega 2560 — controlador PWM de 5 servos MG996R.
_Evitar_: Arduino Mega, la mega

## Relationships

- **Tracking** produce **Landmarks** (21 puntos 3D)
- **IK** convierte **Landmarks** → 5 **Servo** angles
- **Bridge** reenvía comandos **M<idx> <angle>** de **Qualcomm** a **Mega**
- **Record** captura **Landmarks** + **Angles** → archivo JSON
- **Replay** reproduce archivo JSON → **3D Hand** + **Servo** indicators

## Communication Path

```
Browser → WebSocket → Flask (Qualcomm) → TCP:7500 → SOCAT → USB → STM32 Serial → Bridge → Serial1 → Mega → PWM → Servos
```

## Flagged ambiguities

- "Mano virtual" / "Mano 3D" — resuelto: **3D Hand**
- "Grabar/Record" — resuelto: **Record**
- "Reproducir/Replay" — resuelto: **Replay**

## Example dialogue

> **Dev:** "Cuando hago **Tracking**, ¿los **Landmarks** van directo a los **Servos**?"
> **Domain expert:** "No. **Tracking** → **IK** → **Bridge** → **Mega** → **Servos**. El **IK** convierte los landmarks en ángulos antes de enviarlos."
