# Bitácora de Errores y Soluciones

## 2026-05-06 — Sesión Inicial

### Error: UNO Q no detectado por USB
**Síntoma:** Placa encendida (LEDs funcionando) pero `lsusb` no muestra dispositivo.
**Causa:** Cable USB sin datos (cable de carga de móvil sin pines D+/D-).
**Solución:** Comprar cable USB-C a USB-C con datos.
**Lección:** Verificar siempre `lsusb` y `dmesg` para descartar cable antes de asumir fallo de placa.

### Error: Permisos del dispositivo USB (udev)
**Síntoma:** `lsusb` no muestra la placa aunque el USB tree de sysfs sí. App Lab no puede hacer provisioning.
**Causa:** `/dev/bus/usb/002/00X` pertenece a `root:root` modo 0664. El `arduino-flasher-cli` no puede escribir.
**Solución:** Crear regla udev:
```
SUBSYSTEM=="usb", ATTR{idVendor}=="2341", ATTR{idProduct}=="0078", MODE="0666"
```
**Archivo:** `/etc/udev/rules.d/99-arduino-uno-q.rules`
**Lección:** Las placas nuevas necesitan reglas udev explícitas para el provisioning USB.

### Error: `/dev/ttyACM0` Permission denied
**Síntoma:** `stty` y `cat` devuelven "Permiso denegado" en ttyACM0.
**Causa:** Usuario está en grupo `dip`, no `dialout` (el grupo del dispositivo).
**Solución:** `sudo usermod -a -G dialout $USER`. Requiere re-login o `newgrp dialout`.
**Workaround:** `sudo chmod 666 /dev/ttyACM0` para la sesión actual.

### Nota: ttyACM0 = STM32U585, no Qualcomm
El ttyACM0 del UNO Q es el puerto serie del microcontrolador STM32U585 (para sketch uploads y Serial Monitor de App Lab/Arduino IDE). La consola Linux del Qualcomm NO está expuesta vía USB serial.
Para acceder al Qualcomm Linux: esperar a que arranque y conectarse vía WiFi o SSH.

### Error: Arduino App Lab "New Board" no responde
**Síntoma:** App Lab detecta la placa pero al pulsar "New Board" no ocurre nada.
**Causa 1:** Permisos USB (ver arriba).
**Causa 2:** El provisioning inicial tarda varios minutos.
**Solución:** Arreglar udev + esperar a que termine el flasheo del SO.

### Error: pip "externally-managed-environment"
**Síntoma:** `pip3 install` falla con "error: externally-managed-environment".
**Causa:** Debian 13 en UNO Q aplica PEP 668. Paquetes del sistema gestionan /usr.
**Solución:** Usar `pip3 install --break-system-packages <paquete>`.
**Lección:** Sistemas Debian modernos requieren `--break-system-packages` o venv.

### Error: UNO Q pierde WiFi tras configuración AP
**Síntoma:** La IP 192.168.31.12 deja de responder tras intentar conexión al AP RobotHand.
**Causa:** Posible conflicto entre modo AP (hostapd) y modo cliente WiFi simultáneos.
**Estado:** Pendiente de resolver.

### Descubrimiento: Arquitectura de comunicación Qualcomm ↔ STM32
- La UART física entre chips es `/dev/ttyHS1` @ 115200 baud = LPUART1 en el STM32U585
- `arduino-router.service` gestiona esta comunicación (socket Unix)
- `/dev/ttyGS0` es el USB Gadget Serial (monitor), NO la UART directa
- `arduino-router-cli` usa MsgPack RPC pero tiene bug de display (panic en int8)
- Mapeo: `Serial = Serial2 = LPUART1`. `Serial1 = USART1` (D0/D1 UNO headers)
- `Serial` = Router Bridge (RPC). `Serial2` = acceso directo a LPUART1

### Error: LED matrix muestra logo Arduino en vez de iconos
**Síntoma:** Al activar el tracking, los LEDs muestran el logo de Arduino/corazón en vez de los iconos de pose.
**Causa 1:** `systemctl stop arduino-router` ejecuta ExecStopPost (GPIO38 toggle) que resetea el STM32.
**Causa 2:** `systemctl start arduino-router` ejecuta ExecStartPre (GPIO37=0) que también resetea el STM32.
**Causa 3:** `Serial2.begin()` compite con el router por LPUART1 y falla (Zephyr solo permite un proceso por UART).
**Solución:**
1. Drop-in systemd para vaciar ExecStopPost y ExecStartPre:
   ```
   /etc/systemd/system/arduino-router.service.d/20-no-reset.conf:
   [Service]
   ExecStopPost=
   ExecStartPre=
   ```
2. Parar el router antes de subir el sketch → `Serial2.begin()` abre LPUART1 sin conflicto
3. Flask escribe a `/dev/ttyHS1` directamente, sin parar el router
**Estado:** Solución parcial. LED muestra smiley fijo. Identificar si `Serial2.begin()` realmente tuvo éxito pendiente de verificar con conexión Mega mañana.

### Error: Dedos inexactos y demasiado sensibles
**Síntoma:** Tracking de dedos salta bruscamente. Los ángulos no reflejan la posición real.
**Causa:** IK en 2D + sin rate-limiting + deadzone insuficiente + fórmula pulgar incorrecta.
**Solución (basada en investigación de repos GitHub):**
| Parámetro | Antes | Ahora |
|---|---|---|
| Vectores IK | 2D (x,y) | 3D (x,y,z) |
| Dead zone dedos | 5° | 8° |
| Dead zone pulgar | 5° | 12° |
| Pulgar | Ángulo muñeca | Eje X (90% repos) |
| Rate limiting | No | Max 5°/frame |
| Estabilidad | No | 3 frames iguales |
| Sensibilidad | 100% | 85% |
| Calibración | Genérica | Per-finger (open/closed) |
| EMA α | 0.20 | 0.25 |
**Lección:** 90% de los repos usan comparación de eje X para el pulgar, no cálculos de ángulos complejos. La calibración por dedo es esencial porque cada servo tiene montaje diferente.

### Error: LEDs apagados tras subir sketch por OpenOCD
**Síntoma:** Tras flashear el STM32, la matriz LED queda apagada. Solo funciona tras un reboot completo.
**Causa:** OpenOCD no reinicia correctamente todos los periféricos del STM32 (GPIO de la matriz LED queda en estado incorrecto).
**Solución:** Hacer `sudo reboot` tras cada flash. El power-cycle completo inicializa todos los periféricos.
**Lección:** OpenOCD por SWD es útil para debug pero no sustituye un reset de hardware completo.

### Error: LEDs muestran formas ilegibles / "desbordamiento"
**Síntoma:** Los iconos 12×8 definidos con `rowsToFrame` muestran patrones irreconocibles, parecen "desbordados".
**Causa 1:** La función `rowsToFrame` tenía overflow de bits al empaquetar 12 bits en uint32_t.
**Causa 2:** El `reverse()` de los uint32_t producía un mapeo de píxeles impredecible (no documentado).
**Causa 3:** El formato de bits (row-major vs column-major) no coincide con el hardware real.
**Solución:** Abandonar el mapeo manual de bits. Usar **ArduinoGraphics** con fuente `Font_5x7` para números y `matrix.point()` para la carita. Cero cálculos de bits, renderizado perfecto.
**Lección:** Para matrices LED, usar siempre la librería de gráficos de alto nivel. El mapeo de bits a hardware es frágil y no documentado.

### Error: `Serial2.begin()` crashea el STM32U585
**Síntoma:** La matriz LED no enciende, el sketch parece no ejecutarse.
**Causa:** `Serial2` usa LPUART1, el mismo UART que el `arduino-router`. En Zephyr OS, solo un proceso puede abrir un UART. `Serial2.begin()` genera una excepción al intentar abrir LPUART1 ya ocupado.
**Solución:** Eliminar `Serial2` del sketch. Usar solo `Serial` (USB CDC ACM). La comunicación Qualcomm→STM32 va por TCP:7500 → SOCAT → ttyGS0 → USB → Serial.
**Lección:** En el UNO Q, `Serial = Serial2 = LPUART1`. `Serial` usa el router bridge (RPC), `Serial2` es acceso directo. No pueden coexistir.

### Error: Pulgar no se cuenta en el LED (siempre ignorado)
**Síntoma:** Los otros 4 dedos se cuentan bien, pero el pulgar nunca aparece en el número de dedos levantados aunque esté extendido.
**Causa:** El rango del servo del pulgar es 140°-152° (extendido-cerrado), pero el umbral de "abierto" era <50° para todos los dedos. El pulgar NUNCA baja de 140°, por lo que nunca se contaba.
**Solución:** Umbral separado en `countFingersUp()`: pulgar <145°, resto <50°. Esto coincide con el rango real reportado por el IK (140° extendido, 152° cerrado).
**Lección:** Cada servo tiene un rango de montaje distinto. Los umbrales deben calibrarse por dedo en el hardware final.

### Error: Carita smiley se ve como "corazón raro"
**Síntoma:** El icono de smiley dibujado con `matrix.circle()` y `matrix.point()` se ve deformado.
**Causa:** `matrix.circle()` con radio 4 en una matriz 12×8 produce una elipse deformada (los píxeles no son cuadrados).
**Solución:** Dibujar la carita píxel a píxel con `matrix.point(x, y)` controlando cada LED individualmente. 22 puntos que forman una cara reconocible.
**Lección:** En matrices de baja resolución, el dibujo píxel a píxel da mejores resultados que las primitivas geométricas.

### Error: Botón "Iniciar" desaparece / no funciona
**Síntoma:** Tras reestructurar la web con Three.js y Chart.js, el botón ▶ Iniciar no aparece o no hace nada al pulsarlo.
**Causa 1:** `overflow: hidden` en `.card` recortaba la fila de botones.
**Causa 2:** `<script src="three.js">` bloqueaba la carga de la página si la CDN iba lenta → el `<script type="module">` nunca se ejecutaba → `window.start` no se definía.
**Causa 3:** `new Chart()` o `new THREE.Scene()` lanzaban errores que detenían el módulo antes de asignar `window.start`.
**Solución:**
1. Quitar `overflow: hidden` de `.card`
2. Cargar Three.js y Chart.js **asíncronamente** con inyección de `<script>` + onload (nunca bloquear la carga)
3. Definir `window.start` al principio del módulo, antes de cualquier inicialización opcional
4. Envolver toda la inicialización de CDNs en try-catch
**Lección:** Los scripts de CDN externos NUNCA deben bloquear la carga. Siempre carga asíncrona con fallback.

### Error: Cámara no se muestra (pero tracking funciona)
**Síntoma:** MediaPipe rastrea la mano, los landmarks se detectan, pero el elemento `<video>` no muestra la imagen de la cámara.
**Causa 1:** El canvas de overlay se redimensionaba en cada frame (`canv.width=video.videoWidth`), causando parpadeo.
**Causa 2:** Sin `muted` en el `<video>`, el autoplay falla en algunos navegadores.
**Causa 3:** El CSS global `video, canvas { position:absolute }` aplicaba también al canvas de Three.js, sacándolo de su contenedor.
**Solución:**
1. Redimensionar el canvas UNA SOLA VEZ (en `start()`, no en cada frame de `loop()`)
2. Añadir `muted playsinline` al tag `<video>`
3. Cambiar `video, canvas` a `.video-wrap video, .video-wrap canvas` para no afectar al Three.js
4. Añadir `pointer-events:none` al canvas de tracking
**Lección:** Los selectores CSS globales para `canvas` afectan a TODOS los canvas de la página (incluyendo los de librerías externas).

### Error: Mano 3D se sale de su contenedor
**Síntoma:** El canvas de Three.js aparece fuera del `div.three-wrap`, ignorando `overflow:hidden` y `aspect-ratio`.
**Causa:** El CSS `video, canvas { position:absolute }` aplicaba `position:absolute` al canvas de Three.js, sacándolo del flujo normal del contenedor.
**Solución:** Limitar los selectores CSS a `.video-wrap canvas`. Para Three.js: `.three-wrap canvas { display:block; width:100%; height:100%; }` y `setSize()` con tamaño fijo (400×200), dejando que CSS escale.
**Lección:** Three.js establece `width/height` inline en el canvas vía `setSize()`. Hay que usar CSS con `width:100%; height:100%` y `display:block` para que el canvas llene el contenedor.

### Error: Rendimiento cae durante el tracking
**Síntoma:** La página se vuelve lenta, los fps bajan.
**Causa 1:** Resolución de cámara demasiado alta (640×480).
**Causa 2:** `backdrop-filter: blur(14px)` en todas las tarjetas consume mucha GPU.
**Causa 3:** Envío de WebSocket cada 30ms (demasiado frecuente).
**Causa 4:** `setPixelRatio(Math.min(devicePixelRatio, 2))` en Three.js.
**Solución:**
1. Reducir cámara a 480×360
2. Quitar `backdrop-filter` (solo estética, alto coste GPU)
3. Aumentar intervalo de envío a 50ms
4. `setPixelRatio(1)` en Three.js
**Lección:** En dispositivos móviles/embebidos, priorizar rendimiento sobre estética. Cada filtro CSS cuesta fps.

---
*Última actualización: 2026-05-07 01:30*
