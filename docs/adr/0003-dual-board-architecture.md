# Arquitectura Dual-Board (UNO Q + Mega)

El sistema usa dos placas: UNO Q (Qualcomm + STM32) como cerebro y Arduino Mega 2560 como controlador PWM dedicado de los 5 servos MG996R.

**Por qué no solo el UNO Q:**
- El UNO Q tiene 6 pines PWM (D3, D5, D6, D9, D10, D11) — técnicamente suficientes para 5 servos
- Pero los servos MG996R consumen ~2.5A cada uno bajo carga (12.5A total pico)
- Alimentar 5 servos desde el UNO Q compartiría fuente con el Qualcomm → riesgo de brownout y ruido en la señal
- El PWM del UNO Q es 3.3V; el Mega proporciona 5V limpio, dentro del rango óptimo de los MG996R (umbral TTL ~2.5V)
- Separar la etapa de potencia del cómputo aísla fallos: un servo quemado no apaga el cerebro del sistema

**Costo aceptado:** 3 cables dupont adicionales (GND, TX, RX) entre placas, y un sketch más que mantener.
