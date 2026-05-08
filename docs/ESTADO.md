# Estado del Proyecto — 2026-05-08

## Servidor activo

| Dato | Valor |
|---|---|
| IP | 192.168.31.12 (WiFi Xiaomi) |
| URL | https://192.168.31.12:3000 |
| Flask | Activo (systemd robot-hand.service) |
| SOCAT | Activo (TCP:7500 ↔ USB serial) |

## Lo que funciona

- ✅ Tracking de mano con **MediaPipe.js** en navegador
- ✅ **IK 3D** — conversión landmarks → ángulos de servo (Python)
- ✅ **LED Matrix** — números 0-5 + smiley (ArduinoGraphics)
- ✅ **3D Hand** — mano 3D con Three.js (carga asíncrona)
- ✅ **Chart.js** — gráfica de 5 ángulos en tiempo real
- ✅ **Record/Replay** — grabación con deep copy + reproducción con rAF
- ✅ **WebSocket** con indicador de latencia en ms
- ✅ **Glassmorphism** + responsive (desktop cámara+3D lado a lado, mobile apilado)
- ✅ **WiFi AP** (RobotHand) como backup
- ✅ **PDF documentación** (79 KB)
- ✅ **GitHub** repo público

## Lo pendiente

| Tarea | Prioridad |
|---|---|
| Conectar Mega 2560 (3 cables dupont) | 🔴 Crítica |
| Subir sketch Mega (mega_servos.ino) | 🔴 Crítica |
| Subir sketch STM32 (bridge.ino) | 🔴 Crítica |
| Identificar pines de los 5 servos en el Mega | 🔴 Crítica |
| Calibrar umbrales de pulgar con el brazo real | 🟡 Alta |
| Probar cadena completa: cámara → servos | 🔴 Crítica |

## Archivos clave

| Archivo | Descripción |
|---|---|
| `qualcomm/server.py` | Flask + WebSocket + IK + serial |
| `qualcomm/static/index.html` | Frontend completo |
| `qualcomm/v1-browser/` | Backup v1 (navegador) |
| `qualcomm/v2-server/` | Experimental v2 (server-side) |
| `stm32_sketch/bridge/bridge.ino` | STM32U585 bridge + LED matrix |
| `mega_sketch/servos/mega_servos.ino` | Mega servo control |
| `docs/brazo-robotico.pdf` | Documentación técnica (79 KB) |
| `docs/errores-soluciones.md` | Bitácora (22 errores) |
| `CONTEXT.md` | Glosario del dominio |

## Skills disponibles

- **El Maestro** (TDD)
- **Bug Doctor** (diagnose)
- **El de las Gafas** (grill-with-docs)

## Notas para el siguiente chat

- El servidor está en auto-arranque. Si se reinicia el UNO Q, Flask se levanta solo.
- SOCAT hay que iniciarlo manualmente: `sudo socat file:/dev/ttyGS0,raw,echo=0,b115200,crtscts=0 tcp:127.0.0.1:7500 &`
- El router (`arduino-router.service`) tiene un drop-in que vacía ExecStopPost/ExecStartPre para evitar resets del STM32.
- Password SSH y sudo del UNO Q: 1g51yF52g0**
- La contraseña de sudo del portátil: 5915
