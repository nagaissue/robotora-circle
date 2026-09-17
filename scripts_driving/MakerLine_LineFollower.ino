#include <Arduino.h>

// -----------------------------------------------------------------------------
// ピン設定 (参照元 linetrace_esp.ino に準拠)
// -----------------------------------------------------------------------------
// MakerLine アナログ出力ピン
const int MAKERLINE_PIN = 34; // 34番ピン (ADC1_CH6) - 入力専用ピン

// モーター1 (M1: 左モーター)
const int LEFT_STEP_PIN = 19;
const int LEFT_DIR_PIN  = 18;

// モーター2 (M2: 右モーター)
const int RIGHT_STEP_PIN = 17;
const int RIGHT_DIR_PIN  = 16;

// -----------------------------------------------------------------------------
// 制御パラメータ
// -----------------------------------------------------------------------------
const int BASE_STEP_DELAY = 1200; // 基本ステップ間隔 (マイクロ秒)
const int MIN_STEP_DELAY  = 600;  // 最小ステップ間隔（最高速）
const int MAX_STEP_DELAY  = 2500; // 最大ステップ間隔（最低速）

// MakerLineのアナログ出力の中央基準値 (0〜4095)
const int CENTER_VAL = 2048;

void setup() {
  Serial.begin(115200);

  // ピンモード設定
  pinMode(MAKERLINE_PIN, INPUT);
  
  pinMode(LEFT_STEP_PIN, OUTPUT);
  pinMode(LEFT_DIR_PIN, OUTPUT);
  pinMode(RIGHT_STEP_PIN, OUTPUT);
  pinMode(RIGHT_DIR_PIN, OUTPUT);

  // 前進方向の設定 (必要に応じてHIGH/LOWを反転してください)
  digitalWrite(LEFT_DIR_PIN, HIGH);
  digitalWrite(RIGHT_DIR_PIN, LOW);

  // ADCの設定 (ESP32)
  analogSetAttenuation(ADC_11db); // 0V〜3.3Vの範囲に設定
}

void loop() {
  // 1. センサー値の読み取り
  int sensorVal = analogRead(MAKERLINE_PIN);

  // 2. 偏差の計算 (中央値からのズレ)
  int error = sensorVal - CENTER_VAL;

  // 3. 簡易P制御 (比例制御) による左右の速度調整
  float kP = 0.5; // 比例ゲイン
  int correction = (int)(error * kP);

  int leftDelay  = BASE_STEP_DELAY + correction;
  int rightDelay = BASE_STEP_DELAY - correction;

  // 範囲制限
  leftDelay  = constrain(leftDelay, MIN_STEP_DELAY, MAX_STEP_DELAY);
  rightDelay = constrain(rightDelay, MIN_STEP_DELAY, MAX_STEP_DELAY);

  // 4. ステッピングモーターの駆動パルス生成
  digitalWrite(LEFT_STEP_PIN, HIGH);
  digitalWrite(RIGHT_STEP_PIN, HIGH);
  delayMicroseconds(10); // パルス幅
  digitalWrite(LEFT_STEP_PIN, LOW);
  digitalWrite(RIGHT_STEP_PIN, LOW);

  int minDelay = min(leftDelay, rightDelay);
  delayMicroseconds(minDelay);
  
  if (leftDelay > minDelay) {
    delayMicroseconds(leftDelay - minDelay);
  }
  if (rightDelay > minDelay) {
    delayMicroseconds(rightDelay - minDelay);
  }
}
