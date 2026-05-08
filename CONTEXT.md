# Brazo Robótico — Domain Context

Sistema de control de una mano robótica de 5 dedos mediante visión por computador.

## Language

**3D Hand**:
Representación tridimensional de la mano con Three.js en el frontend.
_Evitar_: mano virtual, mano 3D, modelo 3D

**Angles**:
Vector de 5 enteros (0-180°) que representan la posición objetivo de cada Servo, resultado del IK. Viajan como Command `M<idx> <angle>`.
_Evitar_: posiciones, valores de servo

**Bridge**:
Sketch del STM32U585 que actúa como puente UART entre Qualcomm Linux y Arduino Mega. También controla la LED Matrix mostrando el conteo de dedos levantados.
_Evitar_: puente, pasarela

**Command**:
Mensaje serial con formato `M<idx> <angle>\n` que viaja desde Flask hasta el Mega a través de toda la cadena de comunicación.
_Evitar_: mensaje, trama, paquete, instrucción

**IK (Inverse Kinematics)**:
Conversión de 21 landmarks de MediaPipe a 5 ángulos de servo (0-180°).
_Evitar_: cinemática, mapeo

**Interpolation**:
Rampa suave de 1°/12ms con la que el Mega mueve cada Servo desde su ángulo actual hacia el ángulo objetivo, evitando saltos bruscos.
_Evitar_: suavizado, rampa, slew rate

**Landmarks**:
Los 21 puntos 3D (x, y, z) que produce el Tracking con MediaPipe. Son el input del IK.
_Evitar_: puntos, keypoints, coordenadas, marcadores

**LED Matrix**:
Matriz de 12×8 LEDs rojos integrada en el UNO Q. Muestra el número de dedos levantados (1-5) o un smiley 🙂 cuando no hay tracking activo. Controlada desde el Bridge con ArduinoGraphics.
_Evitar_: display, pantalla LED, led panel, matriz

**Mega**:
Arduino Mega 2560 — controlador PWM de 5 servos MG996R.
_Evitar_: Arduino Mega, la mega

**Qualcomm**:
SoC QRB2210 dentro del UNO Q que ejecuta Debian Linux, Flask y el servidor WebSocket.
_Evitar_: el Linux, la CPU, el procesador, el ARM

**Record**:
Grabación de frames (landmarks + ángulos) para reproducción posterior.
_Evitar_: grabar, grabación

**Replay**:
Reproducción de una grabación previamente almacenada.
_Evitar_: reproducir, reproducción

**Router**:
Servicio `arduino-router` que gestiona la comunicación entre Qualcomm y STM32 vía LPUART1. Actualmente **bypasseado** en favor de SOCAT + USB CDC ACM para evitar conflictos de Zephyr con LPUART1.
_Evitar_: enrutador

**Servo**:
Actuador MG996R que mueve un dedo. Recibe ángulo 0-180° vía PWM.
_Evitar_: motor, actuador

**SOCAT**:
Herramienta que puentea TCP:7500 ↔ USB Gadget Serial, permitiendo que Flask hable con el Bridge sin usar el Router. Sustituye de facto al `arduino-router-serial.service`.
_Evitar_: proxy serial, puente serial, túnel

**Tracking**:
Detección en tiempo real de la mano humana mediante MediaPipe (21 landmarks).
_Evitar_: detección, seguimiento

**UNO Q**:
Arduino UNO Q (ABX00162) — placa con Qualcomm QRB2210 (Linux) + STM32U585 (MCU).
_Evitar_: placa, arduino

## Relationships

- **Tracking** produce **Landmarks** (21 puntos 3D)
- **IK** convierte **Landmarks** → 5 **Angles**
- **Angles** viajan como **Command** `M<idx> <angle>`
- **Qualcomm** envía **Command** vía **SOCAT** → **Bridge** → **Mega**
- **Mega** aplica **Interpolation** hacia cada **Servo**
- **Bridge** controla la **LED Matrix** con el conteo de dedos
- **Record** captura **Landmarks** + **Angles** → archivo JSON
- **Replay** reproduce archivo JSON → **3D Hand** + **Servo** indicators

## Communication Path

```
Browser → WebSocket → Flask (Qualcomm) → TCP:7500 → SOCAT → USB CDC ACM → STM32 Serial → Bridge → Serial1 → Mega Serial3 → PWM → Servos
```

## Example dialogue

> **Dev:** "Cuando hago **Tracking**, ¿los **Landmarks** van directo a los **Servos**?"
> **Domain expert:** "No. **Tracking** → **IK** → **SOCAT** → **Bridge** → **Mega** → **Servos**. El **IK** convierte los **Landmarks** en **Angles**. La **Interpolation** del Mega suaviza el movimiento 1°/12ms. Y si la **LED Matrix** muestra 🙂, no hay tracking activo."
> **Dev:** "¿Por qué hay un **Mega** aparte si el **UNO Q** tiene pines PWM?"
> **Domain expert:** "Para aislar la etapa de potencia. Los servos MG996R pueden consumir 2.5A cada uno bajo carga — no queremos eso cerca del **Qualcomm**."
