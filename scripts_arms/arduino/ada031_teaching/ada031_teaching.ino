#include <Servo.h>
#include <EEPROM.h>

// ADA031 5-DOF Robotic Arm Pins (Default Adeept Shield configuration)
// Adjust if your wiring differs
const int servoPins[5] = {2, 3, 4, 5, 6}; 
Servo servos[5];

// Current servo angles
int currentAngles[5] = {90, 90, 90, 90, 90};

// EEPROM layout constants
const int MAX_POSES = 180; // Maximum number of poses (180 poses * 5 bytes = 900 bytes < 1024 bytes)
const int ADDR_COUNT = 0;  // 2 bytes for stored pose count
const int ADDR_DATA = 4;   // Pose data starting address

int poseCount = 0;

void setup() {
  Serial.begin(9600);
  
  // Attach servos and move to home position
  for (int i = 0; i < 5; i++) {
    servos[i].attach(servoPins[i]);
    servos[i].write(currentAngles[i]);
  }

  // Load pose count from EEPROM
  loadPoseCount();
  Serial.print("READY. Saved poses: ");
  Serial.println(poseCount);
}

void loop() {
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();

    if (command.startsWith("M:")) {
      // Move command: M:v1,v2,v3,v4,v5
      parseAndMove(command.substring(2));
    } 
    else if (command == "SAVE") {
      saveCurrentPose();
    } 
    else if (command == "PLAY") {
      playSequence();
    } 
    else if (command == "RESET") {
      resetEEPROM();
    } 
    else if (command == "STATUS") {
      printStatus();
    }
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

  if (idx >= 4) { // Validated 5 values received
    for (int i = 0; i < 5; i++) {
      values[i] = constrain(values[i], 0, 180);
      currentAngles[i] = values[i];
      servos[i].write(currentAngles[i]);
    }
    Serial.println("OK:MOVED");
  } else {
    Serial.println("ERR:INVALID_ARGS");
  }
}

void saveCurrentPose() {
  if (poseCount >= MAX_POSES) {
    Serial.println("ERR:EEPROM_FULL");
    return;
  }

  int addr = ADDR_DATA + (poseCount * 5);
  for (int i = 0; i < 5; i++) {
    EEPROM.write(addr + i, (byte)currentAngles[i]);
  }

  poseCount++;
  updatePoseCount();
  
  Serial.print("OK:SAVED:");
  Serial.println(poseCount);
}

void playSequence() {
  if (poseCount == 0) {
    Serial.println("ERR:NO_POSES");
    return;
  }

  Serial.println("OK:PLAY_START");
  
  for (int p = 0; p < poseCount; p++) {
    int addr = ADDR_DATA + (p * 5);
    for (int i = 0; i < 5; i++) {
      int angle = EEPROM.read(addr + i);
      currentAngles[i] = angle;
      servos[i].write(angle);
    }
    // Delay between poses for smooth movement (adjust as needed)
    delay(800); 
  }

  Serial.println("OK:PLAY_END");
}

void resetEEPROM() {
  poseCount = 0;
  updatePoseCount();
  Serial.println("OK:RESET");
}

void loadPoseCount() {
  byte high = EEPROM.read(ADDR_COUNT);
  byte low = EEPROM.read(ADDR_COUNT + 1);
  poseCount = (high << 8) | low;
  
  // Initialize if uninitialized (EEPROM contains 0xFF)
  if (poseCount < 0 || poseCount > MAX_POSES) {
    poseCount = 0;
    updatePoseCount();
  }
}

void updatePoseCount() {
  EEPROM.write(ADDR_COUNT, (byte)(poseCount >> 8));
  EEPROM.write(ADDR_COUNT + 1, (byte)(poseCount & 0xFF));
}

void printStatus() {
  Serial.print("STATUS:Poses=");
  Serial.print(poseCount);
  Serial.print(",Angles=");
  for (int i = 0; i < 5; i++) {
    Serial.print(currentAngles[i]);
    if (i < 4) Serial.print(",");
  }
  Serial.println();
}
