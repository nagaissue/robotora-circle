// ライントレースセンサ読み取り用Arduinoプログラム
#include<ArduinoJson.h>

void setup() {
  Serial.begin(9600);

  pinMode(2, INPUT);
  pinMode(3, INPUT);
  pinMode(4, INPUT);
  pinMode(5, INPUT);
  pinMode(6, INPUT);
  pinMode(7, INPUT);
  pinMode(8, INPUT);
  pinMode(9, INPUT);
}

void loop() {
  while (true) {
    if(Serial.available() > 0){
      String data = Serial.readStringUntil('\n');
      StaticJsonDocument<200> Rdoc;
      deserializeJson(Rdoc, data);
      String Rdata = Rdoc["cmd"];
      if (Rdoc["cmd"] == "GET") {
        break;
      }
    }
  }
  int line[8] = { 0 };  
  line[0] = digitalRead(2);
  line[1] = digitalRead(3);
  line[2] = digitalRead(4);
  line[3] = digitalRead(5);
  line[4] = digitalRead(6);
  line[5] = digitalRead(7);
  line[6] = digitalRead(8);
  line[7] = digitalRead(9);
 
  StaticJsonDocument<200> Sdoc;
  Sdoc["line0"] = line[0];
  Sdoc["line1"] = line[1];
  Sdoc["line2"] = line[2];
  Sdoc["line3"] = line[3];
  Sdoc["line4"] = line[4];
  Sdoc["line5"] = line[5];
  Sdoc["line6"] = line[6];
  Sdoc["line7"] = line[7];

  serializeJson(Sdoc, Serial);
  Serial.println();
}
