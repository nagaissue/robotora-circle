#include <TimerOne.h>

int irq_timing = 100;

char step_start_flg_right = 0;
int pulse_width_right = 10;
char width_cnt_right = 0;
char pulse_stat_right = 0;

char step_start_flg_left = 0;
int pulse_width_left = 10;
char width_cnt_left = 0;
char pulse_stat_left = 0;

const int THRESHOLD = 300;

const int sensorPins[4] = {A1, A2, A3, A4};

// --- 判定関数群 ---
bool allOne(int s[4]) {
  for (int i = 0; i < 4; i++) {
    if (s[i] != 1) return false;
  }
  return true;
}

bool isRightTurn_2(int s[4]) {
  return (s[0]==1 && s[1]==0 &&
          s[2]==0 && s[3]==0 );
}

bool isLeftTurn_2(int s[4]) {
  return (s[0]==0 && s[1]==0 &&
          s[2]==0 && s[3]==1);
}

bool isRightTurn(int s[4]) {
  return (s[0]==1 && s[1]==1 &&
          s[2]==0 && s[3]==0 );
}

bool isLeftTurn(int s[4]) {
  return (s[0]==0 && s[1]==0 &&
          s[2]==1 && s[3]==1);
}


void irq_timer1()
{
  if(step_start_flg_right == 1)
  {
    if(pulse_stat_right == 0 && width_cnt_right < pulse_width_right)
    {
      digitalWrite(7, HIGH);
      width_cnt_right++;
      if(width_cnt_right == pulse_width_right)
      {
        pulse_stat_right = 1;
        width_cnt_right = 0;
      }
    }
    else if(pulse_stat_right == 1 && width_cnt_right < pulse_width_right)
    {
      digitalWrite(7, LOW);
      width_cnt_right++;
      if(width_cnt_right == pulse_width_right)
      {
        pulse_stat_right = 0;
        width_cnt_right = 0;
      }
    }
  }
  else
  {
    digitalWrite(7, LOW);
    pulse_stat_right = 0;
  }

  if(step_start_flg_left == 1)
  {
    if(pulse_stat_left == 0 && width_cnt_left < pulse_width_left)
    {
      digitalWrite(8, HIGH);
      width_cnt_left++;
      if(width_cnt_left == pulse_width_left)
      {
        pulse_stat_left = 1;
        width_cnt_left = 0;
      }
    }
    else if(pulse_stat_left == 1 && width_cnt_left < pulse_width_left)
    {
      digitalWrite(8, LOW);
      width_cnt_left++;
      if(width_cnt_left == pulse_width_left)
      {
        pulse_stat_left = 0;
        width_cnt_left = 0;
      }
    }
  }
  else
  {
    digitalWrite(8, LOW);
    pulse_stat_left = 0;
  }
}

void setup() {
  // put your setup code here, to run once:
  pinMode(7, OUTPUT);
  pinMode(8, OUTPUT);
  pinMode(12, OUTPUT);
  pinMode(13, OUTPUT);
//  pinMode(A1, INPUT);
//  pinMode(A2, INPUT);
//  pinMode(A3, INPUT);
//  pinMode(A4, INPUT);
  pinMode(4, INPUT);

  digitalWrite(7, LOW);
  digitalWrite(8, LOW);
  digitalWrite(12, LOW);
  digitalWrite(13, LOW);

  Timer1.initialize(irq_timing);
  Timer1.attachInterrupt(irq_timer1);
}

void loop() {
  // put your main code here, to run repeatedly:
  static unsigned char mode = 0;
  static unsigned char mode_flg = 0;
  static unsigned char once_flg = 0;
  static unsigned char stop_flg = 0;

  // センサ値を配列に格納 (0 or 1 に変換)
  int sensor[4];
  for (int i = 0; i < 4; i++) {
    int value = analogRead(sensorPins[i]);
    sensor[i] = (value > THRESHOLD) ? 1 : 0;
    Serial.print(sensor[i]);
    Serial.print(" ");
  }
  Serial.println();

  // --- 動作判定 ---
  if (allOne(sensor)) {
    mode = 0;              // すべて 1 → 停止
  } else if (isRightTurn_2(sensor)) {
    mode = 2;              //右旋回
  } else if (isLeftTurn_2(sensor)) {
    mode = 3;               // 左旋回
  } else if (isRightTurn(sensor)) {
    mode = 4;               // A0～A2=1, A3～A5=0 → 右折
  } else if (isLeftTurn(sensor)) {
    mode = 5;               // A0～A2=1, A3～A5=0 → 左折
  } else {
    mode = 1;                // その他 → 前進
  }

  if(digitalRead(4) == 0)
  {
    delay(10);
    if(digitalRead(4) == 0)
    {
      mode++;
      if(mode > 11)
        mode = 0;
    }
    while(digitalRead(4) == 0);
  }
  
  if(mode == 0)
  {
    step_start_flg_right = 0;
    step_start_flg_left = 0;

    once_flg = 0;
  }
  else if(mode == 1)
  {
    if(mode_flg != 1)
    {
      once_flg = 0;
      mode_flg = 1;
    }
    
    //前進
    digitalWrite(12, HIGH);
    digitalWrite(13, LOW);

    if(once_flg == 0)
    {
      pulse_width_right = 40;
      pulse_width_left = 40;

      width_cnt_right = 0;
      width_cnt_left = 0;

      once_flg = 1;
    }

    step_start_flg_right = 1;
    step_start_flg_left = 1;
  }
  else if(mode == 2)
  {
    //右旋回
    digitalWrite(12, HIGH);
    digitalWrite(13, LOW);

    if(once_flg == 0)
    {
      pulse_width_right = 30;
      pulse_width_left = 0;

      width_cnt_right = 0;
      width_cnt_left = 0;

      once_flg = 1;
    }
    
    step_start_flg_right = 1;
    step_start_flg_left = 1;
  }
  else if(mode == 3)
  {
    //左旋回
    digitalWrite(12, HIGH);
    digitalWrite(13, LOW);

    if(once_flg == 0)
    {
      pulse_width_right = 0;
      pulse_width_left = 30;

      width_cnt_right = 0;
      width_cnt_left = 0;

      once_flg = 1;
    }
    
    step_start_flg_right = 1;
    step_start_flg_left = 1;
  }
  else if(mode == 4)
  {
    if(mode_flg != 4)
    {
      once_flg = 0;
      mode_flg = 4;
    }
    
    //右折
    digitalWrite(12, HIGH);
    digitalWrite(13, LOW);

    if(once_flg == 0)
    {
      pulse_width_right = 60;
      pulse_width_left = 20;

      width_cnt_right = 0;
      width_cnt_left = 0;

      once_flg = 1;
    }
    
    step_start_flg_right = 1;
    step_start_flg_left = 1;
  }
  else if(mode == 5)
  {
    if(mode_flg != 5)
    {
      once_flg = 0;
      mode_flg = 5;
    }
    
    //左折
    digitalWrite(12, HIGH);
    digitalWrite(13, LOW);

    if(once_flg == 0)
    {
      pulse_width_right = 20;
      pulse_width_left = 60;

      width_cnt_right = 0;
      width_cnt_left = 0;

      once_flg = 1;
    }
    
    step_start_flg_right = 1;
    step_start_flg_left = 1;
  }
}
