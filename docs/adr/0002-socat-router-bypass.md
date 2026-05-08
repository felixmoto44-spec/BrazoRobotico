# Bypass del Router con SOCAT

El UNO Q incluye `arduino-router.service` como gestor nativo de comunicación Qualcomm↔STM32 vía LPUART1 (`/dev/ttyHS1`). Decidimos bypassearlo y usar SOCAT para puentear TCP:7500 ↔ USB Gadget Serial (`/dev/ttyGS0`).

**Por qué:**
- El router usa MsgPack RPC con bugs documentados (panic en int8)
- `Serial2.begin()` (acceso directo a LPUART1) crashea el STM32 si el router está activo — Zephyr solo permite un proceso por UART
- El router ejecuta GPIO toggles (37=Reset, 38=Shutdown) en ExecStopPost/ExecStartPre que resetean el STM32 al parar/iniciar el servicio

**Consecuencia:** El SOCAT debe iniciarse manualmente tras cada boot: `sudo socat file:/dev/ttyGS0,raw,echo=0,b115200,crtscts=0 tcp:127.0.0.1:7500 &`. El router se mantiene parado con un drop-in systemd que vacía ExecStopPost/ExecStartPre para evitar resets accidentales.
