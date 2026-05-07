/*
 * Arduino Mega 2560 — Control de Servos MG996R ×5
 * Recibe comandos por Serial3 desde el UNO Q
 *
 * Protocolo: M<servo> <angulo>\n
 *
 * Interpolación suave: cada servo se mueve en pasos de 1°
 * hacia el target, evitando saltos bruscos.
 */

#include <Servo.h>

#define NUM_SERVOS 5
#define SERIAL_BAUD 115200
#define STEP_INTERVAL 12
#define MIN_STEP 1

Servo servos[NUM_SERVOS];

int servo_pins[NUM_SERVOS] = {3, 5, 6, 9, 10};
int current_angle[NUM_SERVOS] = {90, 90, 90, 90, 90};
int target_angle[NUM_SERVOS] = {90, 90, 90, 90, 90};
unsigned long last_step = 0;

String input_buffer = "";

void setup() {
  Serial.begin(115200);
  Serial3.begin(SERIAL_BAUD);

  while (!Serial && millis() < 3000);

  for (int i = 0; i < NUM_SERVOS; i++) {
    servos[i].attach(servo_pins[i]);
    servos[i].write(90);
    Serial.print("Servo ");
    Serial.print(i);
    Serial.print(" → pin ");
    Serial.println(servo_pins[i]);
  }

  Serial.println("MEGA-SERVOS: READY");
  Serial.println("Esperando comandos en Serial3...");
}

void loop() {
  while (Serial3.available() > 0) {
    char c = Serial3.read();
    if (c == '\n') {
      procesarComando(input_buffer);
      input_buffer = "";
    } else {
      input_buffer += c;
    }
  }

  if (Serial.available() > 0) {
    char c = Serial.read();
    Serial3.write(c);
  }

  unsigned long now = millis();
  if (now - last_step >= STEP_INTERVAL) {
    last_step = now;
    interpolarServos();
  }
}

void interpolarServos() {
  for (int i = 0; i < NUM_SERVOS; i++) {
    int diff = target_angle[i] - current_angle[i];
    if (abs(diff) < MIN_STEP) continue;
    current_angle[i] += (diff > 0) ? 1 : -1;
    servos[i].write(current_angle[i]);
  }
}

void procesarComando(String cmd) {
  cmd.trim();
  if (cmd.length() == 0) return;

  if (cmd.charAt(0) != 'M') return;

  int spc = cmd.indexOf(' ');
  if (spc == -1) return;

  int idx = cmd.substring(1, spc).toInt();
  int angulo = cmd.substring(spc + 1).toInt();

  if (idx < 0 || idx >= NUM_SERVOS) return;

  target_angle[idx] = constrain(angulo, 0, 180);
}
