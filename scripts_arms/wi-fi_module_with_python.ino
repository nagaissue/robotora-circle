// #define ESP Serial1

const char* ssid = "SSID";
const char* pass = "PASSWORD";

void sendAT(String cmd, int waitTime = 2000)
{
  //ESP.println(cmd);
  Serial.println(cmd);

  unsigned long t = millis();

  while (millis() - t < waitTime)
  {
//    while (ESP.available())
    while (Serial.available())
    {
//      Serial.write(ESP.read());
      Serial.write(Serial.read());
    }
  }
}

void setup()
{
  Serial.begin(115200);
//  ESP.begin(115200);

  delay(3000);

  sendAT("AT");
  sendAT("AT+CWMODE=1");

  sendAT("AT+CWJAP=\"" + String(ssid) + "\",\"" + String(pass) + "\"",10000);

  sendAT("AT+CIPSTART=\"TCP\",\"10.88.119.204\",5000",5000);
}

void loop()
{
  static unsigned long prev = 0;

  if (millis() - prev >= 1000)
  {
    prev = millis();

    String msg = "Arduino\r\n";

    // 送信
    //ESP.print("AT+CIPSEND=");
    //ESP.println(msg.length());

    Serial.print("AT+CIPSEND=");
    Serial.println(msg.length());
    delay(200);

    Serial.print(msg);

    // ESP8266からの応答を表示
    unsigned long start = millis();
    while (millis() - start < 1000)
    {
//      while (ESP.available())
      while (Serial.available())
      {
//        Serial.write(ESP.read());
        Serial.write(Serial.read());
      }
    }
  }
}