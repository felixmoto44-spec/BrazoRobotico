# Brazo Robótico con Arduino UNO Q

## Descripción
Mano robótica con 5 dedos accionados por servomotores MG996R, controlada por Arduino UNO Q + Arduino Mega 2560. El sistema copia movimientos de una mano humana detectados por cámara mediante MediaPipe.

## Hardware

| Componente | Modelo | Función |
|---|---|---|
| Placa principal | Arduino UNO Q (ABX00162) | Control central, WiFi, servidor web, IA |
| Placa secundaria | Arduino Mega 2560 | Control directo de servos (PWM) |
| Servos ×5 | Tower Pro MG996R | Accionamiento de dedos |
| Shield | MEGA Sensor Shield V2.0 | Distribución de señales y alimentación |
| Fuente | Switching 5V / 10A+ | Alimentación de servos y Mega |

### ESPECIFICACIONES UNO Q

| Característica | Valor |
|---|---|
| MPU | Qualcomm Dragonwing QRB2210 (4×Cortex-A53 @ 2GHz) |
| MCU | STM32U585 (Cortex-M33 @ 160MHz) |
| RAM/Linux | 2 GB / Debian Linux |
| PWM pins | 6 (D3, D5, D6, D9, D10, D11) |
| I/O voltaje | 3.3V lógica, 5V tolerante (excepto A0/A1) |
| Conectividad | WiFi 5 dual-band, BT 5.1, USB-C |
| Software | Arduino App Lab (ambos chips) o Arduino IDE 2.0+ (solo MCU) |

### ESPECIFICACIONES MG996R

| Característica | Valor |
|---|---|
| Torque | 9.4 kg·cm (4.8V) / 11 kg·cm (6V) |
| Velocidad | 0.17 seg/60° (4.8V) |
| Ángulo | 0° a 180° |
| Señal PWM | 50 Hz, pulso 1–2 ms |
| Voltaje | 4.8V – 7.2V |
| Corriente | ~2.5A por servo bajo carga |

## Cableado

```
UNO Q GND ──── Mega GND
UNO Q D1 (TX) ──✂── Mega D15 (RX3)
UNO Q D0 (RX) ──✂── Mega D14 (TX3)
```

NOTA: Los servos NUNCA se alimentan desde el pin 5V del UNO Q. Usar fuente externa.
El GND de la fuente externa debe estar conectado al GND común.

## Arquitectura Software

```
  [Cámara móvil/PC]
       │ WiFi
       ▼
  [Flask Server :3000]    ← Qualcomm Linux (Debian)
       │ RPC
       ▼
  [STM32U585 MCU]         ← Zephyr/Arduino sketch
       │ Serial1 (D0/D1)
       ▼
  [Mega 2560 Serial3]      ← Arduino sketch
       │ PWM ×5
       ▼
  [MG996R Servos ×5]      ← Accionamiento dedos
```

### Protocolo Serial UNO Q → Mega

- Baudrate: 115200
- Formato: `M<servo_idx> <angle>\n`
- Ejemplo: `M0 90\n` → servo 0 a 90 grados

## Servos (por confirmar)

| Servo | Dedo | Pin Mega |
|---|---|---|
| 0 | ? | ? |
| 1 | ? | ? |
| 2 | ? | ? |
| 3 | ? | ? |
| 4 | ? | ? |

## Flujo de datos

1. Cámara captura mano humana
2. MediaPipe.js detecta 21 landmarks (x,y,z)
3. WebSocket envía coordenadas al servidor Flask
4. IK Engine convierte landmarks → ángulos de servos
5. Comandos viajan: Flask → RPC → STM32 → UART → Mega → PWM
6. Servos replican posición de dedos

## Comunicación Qualcomm ↔ STM32 (descubierto)

- **Arduino Router** (`arduino-router.service`): Gestor de comunicación entre Qualcomm y STM32U585
  - UART física: `/dev/ttyHS1` @ 115200 baud
  - Socket Unix: `/var/run/arduino-router.sock`
  - CLI: `arduino-router-cli` (MsgPack RPC)
- **Arduino Router Serial** (`arduino-router-serial.service`):
  - Puente SOCAT: `/dev/ttyGS0` ↔ `TCP:127.0.0.1:7500`
  - NOTA: ttyGS0 es el USB Gadget Serial, NO la UART al STM32
- **STM32-usart** driver registrado (major 237) — dispositivo `/dev/ttySTM*` pendiente de creación

## Servicios Arduino en Qualcomm

| Servicio | Función |
|---|---|
| `arduino-router.service` | Comunicación con STM32 vía ttyHS1 |
| `arduino-router-serial.service` | Proxy ttyGS0 → TCP:7500 (monitor) |
| `arduino-app-cli.service` | CLI para App Lab |
| `adbd.service` | Android Debug Bridge daemon |

## Instalación en Qualcomm Linux

```bash
# Dependencias sistema
apt-get update && apt-get install -y python3-pip hostapd dnsmasq

# Dependencias Python (--break-system-packages necesario en Debian)
pip3 install --break-system-packages flask flask-sock pyserial numpy waitress

# WiFi AP
sudo tee /etc/hostapd/hostapd.conf > /dev/null << 'EOF'
interface=wlan0
driver=nl80211
ssid=RobotHand
hw_mode=g
channel=6
wpa=2
wpa_passphrase=robot2026
wpa_key_mgmt=WPA-PSK
EOF

sudo tee /etc/dnsmasq.conf > /dev/null << 'EOF'
interface=wlan0
dhcp-range=192.168.4.10,192.168.4.100,12h
dhcp-option=3,192.168.4.1
dhcp-option=6,192.168.4.1
EOF

sudo ip addr add 192.168.4.1/24 dev wlan0
sudo hostapd -B /etc/hostapd/hostapd.conf
sudo killall dnsmasq; sudo dnsmasq -C /etc/dnsmasq.conf

# Servidor
python3 ~/qualcomm/server.py
```
