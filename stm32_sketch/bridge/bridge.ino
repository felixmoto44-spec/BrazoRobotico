/*
 * STM32U585 Bridge Sketch — Arduino UNO Q
 * Recibe comandos M<x> <angle> → muestra nº dedos en LED matrix.
 * Renderizado con ArduinoGraphics — sin mapeo de bits manual.
 */

#include <ArduinoGraphics.h>
#include <Arduino_LED_Matrix.h>

Arduino_LED_Matrix matrix;

#define MEGA_BAUD 115200
#define POSE_HOLD_MS 400
#define NUM_SERVOS 5

int servo_angle[NUM_SERVOS] = {90, 90, 90, 90, 90};
unsigned long last_cmd_time = 0;
unsigned long last_pose_change = 0;
int current_count = -1;
bool cmd_parsing = false;
int cmd_idx = -1;
char cmd_buffer[8];
uint8_t cmd_pos = 0;

void drawSmiley() {
  matrix.beginDraw();
  matrix.clear();
  matrix.stroke(255, 255, 255);
  matrix.point(2, 5); matrix.point(3, 6); matrix.point(4, 7); matrix.point(5, 7);
  matrix.point(6, 7); matrix.point(7, 6); matrix.point(8, 5);
  matrix.point(2, 1); matrix.point(3, 0); matrix.point(4, 0); matrix.point(5, 0);
  matrix.point(6, 0); matrix.point(7, 0); matrix.point(8, 1);
  matrix.point(1, 3); matrix.point(1, 4); matrix.point(9, 3); matrix.point(9, 4);
  matrix.point(4, 3); matrix.point(6, 3);
  matrix.point(3, 5); matrix.point(7, 5); matrix.point(4, 5); matrix.point(6, 5);
  matrix.endDraw();
}

void drawChar(char ch) {
  matrix.beginDraw();
  matrix.clear();
  matrix.stroke(255, 255, 255);
  matrix.textFont(Font_5x7);
  char s[2] = {ch, 0};
  matrix.text(s, 3, 0);
  matrix.endDraw();
}

int countFingersUp() {
  int count = 0;
  if (servo_angle[0] < 145) count++;
  for (int i = 1; i < NUM_SERVOS; i++)
    if (servo_angle[i] < 50) count++;
  return count;
}

void parseChar(char c) {
  if (c == 'M') {
    cmd_parsing = true; cmd_idx = -1; cmd_pos = 0; cmd_buffer[0] = '\0';
    return;
  }
  if (!cmd_parsing) return;
  if (cmd_idx == -1) {
    if (c >= '0' && c <= '4') cmd_idx = c - '0';
    else cmd_parsing = false;
    return;
  }
  if (c == ' ') return;
  if (c == '\n') {
    if (cmd_idx >= 0 && cmd_idx < NUM_SERVOS && cmd_pos > 0) {
      cmd_buffer[cmd_pos] = '\0';
      int angle = atoi(cmd_buffer);
      angle = constrain(angle, 0, 180);
      servo_angle[cmd_idx] = angle;
      last_cmd_time = millis();
    }
    cmd_parsing = false; cmd_idx = -1; cmd_pos = 0;
    return;
  }
  if (c >= '0' && c <= '9' && cmd_pos < 7) cmd_buffer[cmd_pos++] = c;
  else cmd_parsing = false;
}

void setup() {
  Serial.begin(115200);
  Serial1.begin(MEGA_BAUD);
  while (!Serial && millis() < 3000);
  matrix.begin();
  drawSmiley();
}

void loop() {
  int c;
  if (Serial.available()) {
    c = Serial.read();
    parseChar(c);
    Serial1.write(c);
  }
  if (Serial1.available()) {
    c = Serial1.read();
    Serial.write(c);
  }

  unsigned long now = millis();
  int count;

  if (now - last_cmd_time > 2000)
    count = 0;
  else
    count = countFingersUp();

  if (count != current_count && (now - last_pose_change > POSE_HOLD_MS)) {
    if (count == 0)
      drawSmiley();
    else
      drawChar('0' + count);
    current_count = count;
    last_pose_change = now;
  }
}
