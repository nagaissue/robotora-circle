#include <Servo.h>

// Adeept ADA031 5-DOF Robotic Arm Pins (Custom Configuration)
const int servoPins[5] = {9, 6, 5, 3, 11};
Servo servos[5];

// Current angles for each servo
int currentAngles[5] = {90, 90, 90, 90, 90};

void setup() {
  Serial.begin(115200);
  
  // Attach servos and move to initial home position (90 degrees)
  for (int i = 0; i < 5; i++) {
    servos[i].attach(servoPins[i]);
    servos[i].write(currentAngles[i]);
  }
  
  Serial.println("ADA031_READY");
}

void loop() {
  if (Serial.available() > 0) {
    String inputString = Serial.readStringUntil('\n');
    inputString.trim();

    if (inputString.length() > 0) {
      processCommand(inputString);
    }
  }
}

void processCommand(String cmd) {
  // Protocol format: 
  // 1. Direct Angle Control: "M:a1,a2,a3,a4,a5" (e.g., M:90,45,120,90,90)
  // 2. Status Request: "STATUS"
  // 3. Center/Home: "HOME"

  if (cmd.startsWith("M:")) {
    parseAndMove(cmd.substring(2));
  } 
  else if (cmd == "STATUS") {
    printStatus();
  } 
  else if (cmd == "HOME") {
    moveHome();
  } 
  else {
    Serial.println("ERR:UNKNOWN_COMMAND");
  }
}

void parseAndMove(String data) {
  int values[5];
  int idx = 0;

  while (data.length() > 0 && idx < 5) {
    int commaIdx = data.indexOf(',');
    if (commaIdx == -1) {
      values[idx] = data.toInt();
      break;
    } else {
      values[idx] = data.substring(0, commaIdx).toInt();
      data = data.substring(commaIdx + 1);
    }
    idx++;
  }

  if (idx >= 4) { // Received all 5 values (0 to 4 index)
    for (int i = 0; i < 5; i++) {
      values[i] = constrain(values[i], 0, 180);
      currentAngles[i] = values[i];
      servos[i].write(currentAngles[i]);
    }
    Serial.println("OK");
  } else {
    Serial.println("ERR:INVALID_ARGS");
  }
}

void moveHome() {
  for (int i = 0; i < 5; i++) {
    currentAngles[i] = 90;
    servos[i].write(90);
  }
  Serial.println("OK:HOME");
}

void printStatus() {
  Serial.print("STATUS:ANGLES=");
  for (int i = 0; i < 5; i++) {
    Serial.print(currentAngles[i]);
    if (i < 4) Serial.print(",");
  }
  Serial.println();
}
