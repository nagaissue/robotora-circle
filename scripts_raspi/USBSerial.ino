// ライントレースセンサ読み取り用Arduinoプログラム
#include<ArduinoJson.h>

int line[36][8] = {{0,0,0,1,1,0,0,0}, {0,0,1,1,1,1,0,0},
                   {1,1,1,1,1,1,1,0}, {0,1,1,1,1,1,0,0}, {0,0,1,1,1,0,0,0}, {0,0,0,1,0,0,0,0}, {1,1,1,1,1,1,0,0}, 
                   {0,1,1,1,1,0,0,0}, {0,0,1,1,0,0,0,0}, {1,1,1,1,0,0,0,0}, {0,1,1,0,0,0,0,0}, {1,1,1,1,1,0,0,0}, {0,1,1,1,0,0,0,0}, {0,0,1,0,0,0,0,0},
                   {1,0,0,0,0,0,0,0}, {1,1,0,0,0,0,0,0}, {0,1,0,0,0,0,0,0}, {1,1,1,0,0,0,0,0},
                   {0,0,0,0,1,0,0,0}, {0,0,0,1,1,1,0,0}, {0,0,1,1,1,1,1,0}, {0,1,1,1,1,1,1,1}, {0,0,1,1,1,1,1,1},
                   {0,0,0,0,0,1,0,0}, {0,0,0,0,1,1,1,0}, {0,0,0,1,1,1,1,1}, {0,0,0,0,0,1,1,0}, {0,0,0,0,1,1,1,1}, {0,0,0,0,1,1,0,0}, {0,0,0,1,1,1,1,0},
                   {0,0,0,0,0,0,1,0}, {0,0,0,0,0,1,1,1}, {0,0,0,0,0,0,1,1}, {0,0,0,0,0,0,0,1},
                   {1,1,1,1,1,1,1,1}, {0,1,1,1,1,1,1,0}};
int cnt = 0;

void setup() {
  Serial.begin(9600);
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
  int num = cnt++%36;
  /* シリアルモニタでの動作確認用
  // RaspberryPiと通信するときはコメントアウト
  Serial.print("Line:");
  Serial.print(line[num][0]);
  Serial.print(line[num][1]);
  Serial.print(line[num][2]);
  Serial.print(line[num][3]);
  Serial.print(line[num][4]);
  Serial.print(line[num][5]);
  Serial.print(line[num][6]);
  Serial.println(line[num][7]);
  */

  StaticJsonDocument<200> Sdoc;  
  Sdoc["line0"] = line[num][0];
  Sdoc["line1"] = line[num][1];
  Sdoc["line2"] = line[num][2];
  Sdoc["line3"] = line[num][3];
  Sdoc["line4"] = line[num][4];
  Sdoc["line5"] = line[num][5];
  Sdoc["line6"] = line[num][6];
  Sdoc["line7"] = line[num][7];

  serializeJson(Sdoc, Serial);
  Serial.println();
}
