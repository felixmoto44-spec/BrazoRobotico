# Brazo Robótico con Arduino UNO Q

Control de mano robótica (5 dedos, servos MG996R) mediante visión por computador con **MediaPipe** y **Arduino UNO Q**.

## Arquitectura

```
[Cámara móvil/PC] → WiFi → [UNO Q Flask :3000] → [STM32U585 MCU] → [Mega 2560] → [Servos MG996R ×5]
                              ↑ LED Matrix
                              ↑ (Qualcomm Linux)
```

- **Qualcomm QRB2210** (Debian Linux): Servidor Flask + WebSocket + IK
- **STM32U585 MCU**: LED Matrix (ArduinoGraphics) + puente UART al Mega
- **Arduino Mega 2560**: Control PWM de 5 servos con interpolación suave

## Estructura

```
BrazoRobotico/
├── stm32_sketch/bridge/      # Sketch STM32U585 (LED Matrix + UART bridge)
├── mega_sketch/servos/       # Sketch Mega 2560 (interpolación servos)
├── qualcomm/
│   ├── v1-browser/           # Frontend: MediaPipe.js en navegador
│   ├── v2-server/            # Frontend: frames → UNO Q (experimental)
│   ├── server.py             # Flask + WebSocket + IK
│   ├── static/index.html     # Interfaz web (glassmorphism)
│   └── ...
├── docs/
│   ├── brazo-robotico.pdf    # Documentación técnica
│   ├── informe-completo.md
│   └── errores-soluciones.md # Bitácora
└── .opencode/agents/         # Skills instalados (70 agentes)
```

## Hardware

| Componente | Modelo |
|---|---|
| Placa principal | Arduino UNO Q (ABX00162) |
| Placa secundaria | Arduino Mega 2560 |
| Servos ×5 | Tower Pro MG996R |
| Shield | MEGA Sensor Shield V2.0 |

## Conexión UNO Q ↔ Mega

```
UNO Q GND ──── Mega GND
UNO Q D1 (TX) → Mega D15 (RX3)
UNO Q D0 (RX) ← Mega D14 (TX3)
```

## Protocolo Serial

```
M<servo> <ángulo>\n
Ejemplo: M0 90 → servo 0 a 90°
```

## Uso

1. Conectar UNO Q a la red WiFi
2. Acceder a `https://<IP>:3000`
3. Activar tracking → permite cámara
4. Los servos copian los movimientos de la mano

## Documentación

- [Informe completo (PDF)](docs/brazo-robotico.pdf)
- [Bitácora de errores](docs/errores-soluciones.md)
- Skills: [Agency Agents](https://github.com/msitarzewski/agency-agents) (8 skills activas)

## Licencia

MIT
