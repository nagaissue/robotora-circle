# === ライブラリのインポート ===
from gpiozero import PWMOutputDevice, OutputDevice, DigitalInputDevice
import time

# ==================================================== #
# --- 直接モータを制御する関数（低レベル関数）のクラス --- #
# ==================================================== #
class LowLevelControl:
    # 初期化
    def __init__(self, DIR_PIN, STEP_PIN):
        self.Max2_parse = 5000   # 最高速度
        self.Mid_parse = 3000    # 中速
        self.dir = OutputDevice(DIR_PIN)
        self.step = PWMOutputDevice(STEP_PIN, frequency=self.Mid_parse, initial_value=0)
 
    # モータの回転方向
    def direction(self, dir_val):
        if dir_val == 0:    # 正転 (LOW)
            self.dir.off()
        elif dir_val == 1:  # 逆転 (HIGH)
            self.dir.on()

    # モータの回転速度
    def speed(self, speed):
        if speed < 10:  # speed（回転速度）が10未満は0とみなす
            self.step.value = 0 # PWM停止
        elif speed < 300000:    # speed（回転速度）が定格より速くならないように上限を設定
            self.step.frequency = speed
            self.step.value = 0.5 # デューティ比50%でPWM出力
        else:
            self.step.frequency = self.Max2_parse
            self.step.value = 0.5 # デューティ比50%でPWM出力

# ========================================================= #
# --- 直接的にモータを制御しない関数（高レベル関数）のクラス --- #
# ========================================================= #
class HighLevelCtrl:
    # 初期化
    def __init__(self):
        L_DIR_PIN  = 6      # 左タイヤ回転方向
        R_DIR_PIN  = 12     # 右タイヤ回転方向
        L_STEP_PIN = 13     # 左タイヤ回転速度
        R_STEP_PIN = 16     # 右タイヤ回転速度
        self.LEFT_MOTOR = LowLevelControl(L_DIR_PIN, L_STEP_PIN)   # LowLevelControlクラスのインスタンスを作成
        self.RIGHT_MOTOR = LowLevelControl(R_DIR_PIN, R_STEP_PIN)  # LowLevelControlクラスのインスタンスを作成

        # モータ回転方向
        self.LEFT_FORWARD  = 1     # 左タイヤ正転
        self.LEFT_REVERSE  = 0     # 左タイヤ逆転
        self.RIGHT_FORWARD = 0     # 右タイヤ正転
        self.RIGHT_REVERSE = 1     # 右タイヤ逆転

        # モータの回転速度
        self.Max2_parse = 5000   # 最高速度
        self.Max1_parse = 4000   # 高速
        self.Mid_parse  = 3000   # 中速
        self.Min1_parse = 2000   # 低速
        self.Min2_parse = 1000   # 最低速度

        self.current_l_speed = 0     # 現在の左タイヤ回転速度
        self.current_r_speed = 0     # 現在の右タイヤ回転速度
        self.last_action = ''        # ライントレースの最終動作

    # モータの制御（速度・回転方向）
    def control_motor(self, l_speed, l_dir, r_speed, r_dir, acceleration_step=100):
        # 左右それぞれのモータの回転方向を設定
        self.LEFT_MOTOR.direction(l_dir)
        self.RIGHT_MOTOR.direction(r_dir)
        # 段階的にモータの速度を加減速して目標速度に近づける
        while self.current_l_speed != l_speed or self.current_r_speed != r_speed:
            # 左モータの速度を目標速度に近づける
            if l_speed > self.current_l_speed:
                self.current_l_speed += acceleration_step
            elif l_speed == self.current_l_speed:
                pass
            else:
                self.current_l_speed -= acceleration_step
            # 右モータの速度を目標速度に近づける
            if r_speed > self.current_r_speed:
                self.current_r_speed += acceleration_step
            elif r_speed == self.current_r_speed:
                pass
            else:
                self.current_r_speed -= acceleration_step
            self.LEFT_MOTOR.speed(self.current_l_speed)
            self.RIGHT_MOTOR.speed(self.current_r_speed)
            time.sleep(0.01)  # 加減速のステップごとに少し待つ
        self.last_action = self.action      # ライントレースの最終動作を更新

    def judge_position(self, line):
        # 前進　　「○○●●●●○○」「○○○●●○○○」
        if line == '00011000' or line == '00111100':
            return 'forward'
        # 左旋回　「●●●●●●●○」「○●●●●●○○」「○○●●●○○○」「○○○●○○○○」「●●●●●●○○」
        elif line == '11111110' or line == '01111100' or line == '00111000' or line == '00010000' or line == '11111100':
            return 'left_turn'
        # 左急旋回「○●●●●○○○」「○○●●○○○○」「●●●●○○○○」「○●●○○○○○」「●●●●●○○○」「○●●●○○○○」「○○●○○○○○」
        elif line == '01111000' or line == '00110000' or line == '11110000' or line == '01100000' or line == '11111000' or line == '01110000' or line == '00100000':
            return 'left_sharp_turn'
        # 左超旋回「●○○○○○○○」「●●○○○○○○」「○●○○○○○○」「●●●○○○○○」
        elif line == '10000000' or line == '11000000' or line == '01000000' or line == '11100000':
            return 'left_super_turn'
        # 右旋回　「○○○○●○○○」「○○○●●●○○」「○○●●●●●○」「○●●●●●●●」「○○●●●●●●」
        elif line == '00001000' or line == '00011100' or line == '00111110' or line == '01111111' or line == '00111111':
            return 'right_turn'
        # 右急旋回「○○○○○●○○」「○○○○●●●○」「○○○●●●●●」「○○○○○●●○」「○○○○●●●●」「○○○○●●○○」「○○○●●●●○」
        elif line == '00000100' or line == '00001110' or line == '00011111' or line == '00000110' or line == '00001111' or line == '00001100' or line == '00011110':
            return 'right_sharp_turn'
        # 右超旋回「○○○○○○●○」「○○○○○●●●」「○○○○○○●●」「○○○○○○○●」
        elif line == '00000010' or line == '00000111' or line == '00000011' or line == '00000001':
            return 'right_super_turn'
        # 停止　　「●●●●●●●●」「○●●●●●●○」
        elif line == '11111111' or line == '01111110':
            return 'stop'
        # 想定外
        else:
            return 'unexpected'

    def drive(self, progress):
        # モータの回転速度（定数）
        # ラインセンサから読み取った値がどうなっているか（ラインの踏み方がどうなっているか）を判断して、モータの回転方向と回転速度を制御する
        self.action = self.judge_position(progress)
        if self.action == 'forward':
            print('前進')
            self.control_motor(self.Max1_parse, self.LEFT_FORWARD, self.Max1_parse, self.RIGHT_FORWARD, acceleration_step=200)
        elif 'left' in self.action:
            # モータの回転方向が変わるときは脱調防止のためいったん速度を落としてから目標の速度までもっていく
            if self.last_action != 'forward' and 'left' not in self.last_action:
                self.control_motor(self.Min2_parse, self.LEFT_FORWARD, 0, self.RIGHT_FORWARD, acceleration_step=200)
            if self.action == 'left_turn':
                print('左旋回')
                self.control_motor(self.Mid_parse, self.LEFT_REVERSE, self.Mid_parse, self.RIGHT_FORWARD, acceleration_step=200)
            elif self.action == 'left_sharp_turn':
                print('左急旋回')
                self.control_motor(self.Max1_parse, self.LEFT_REVERSE, self.Max1_parse, self.RIGHT_FORWARD, acceleration_step=200)
            elif self.action == 'left_super_turn':
                print('左超旋回')
                self.control_motor(self.Max2_parse, self.LEFT_REVERSE, self.Max2_parse, self.RIGHT_FORWARD, acceleration_step=200)
        elif 'right' in self.action:
            # モータの回転方向が変わるときは脱調防止のためいったん速度を落としてから目標の速度までもっていく
            if self.last_action != 'forward' and 'right' not in self.last_action:
                self.control_motor(0, self.LEFT_FORWARD, self.Min2_parse, self.RIGHT_FORWARD, acceleration_step=200)
            if self.action == 'right_turn':
                print('右旋回')
                self.control_motor(self.Mid_parse, self.LEFT_FORWARD, self.Mid_parse, self.RIGHT_REVERSE, acceleration_step=200)
            elif self.action == 'right_sharp_turn':
                print('右急旋回')
                self.control_motor(self.Max1_parse, self.LEFT_FORWARD, self.Max1_parse, self.RIGHT_REVERSE, acceleration_step=200)
            elif self.action == 'right_super_turn':
                print('右超旋回')
                self.control_motor(self.Max2_parse, self.LEFT_FORWARD, self.Max2_parse, self.RIGHT_REVERSE, acceleration_step=200)
        elif self.action == 'stop':
            print('停止')
            self.control_motor(0, self.LEFT_FORWARD, 0, self.RIGHT_FORWARD, acceleration_step=1000)
            # ======================= # 
            """パズルエリア アーム制御"""
            # ======================= #
            """
            puzzle_area = PuzzleArea()
            puzzle_area.solve_puzzle()
            # パズルエリア攻略後に後退する動作を追加
            self.action = 'backward'
            self.control_motor(self.Max1_parse, self.LEFT_FORWARD, self.Max1_parse, self.RIGHT_FORWARD, acceleration_step=200)
            time.sleep(1)
            self.action = 'right_sharp_turn'
            self.control_motor(0, self.LEFT_FORWARD, self.Min2_parse, self.RIGHT_FORWARD,acceleration_step=200)
            self.control_motor(self.Max2_parse, self.LEFT_REVERSE, self.Max2_parse, self.RIGHT_FORWARD, acceleration_step=200) 
            """
            time.sleep(1)
        else:
        	print('想定外の事象')
            # 何もしない

# ========================== #
# --- ライン検知関連の定義 --- #
# ========================== #
class LineTrace:
    # 初期化
    def __init__(self):
        # ラインセンサ関連GPIOピン設定 (ピン番号)
        SENSOR_PIN1 = 14    # ●○○○○○○○
        SENSOR_PIN2 = 15    # ○●○○○○○○
        SENSOR_PIN3 = 18    # ○○●○○○○○
        SENSOR_PIN4 = 23    # ○○○●○○○○
        SENSOR_PIN5 = 22    # ○○○○●○○○
        SENSOR_PIN6 = 25     # ○○○○○●○○
        SENSOR_PIN7 = 8     # ○○○○○○●○
        SENSOR_PIN8 = 7     # ○○○○○○○●
        self.sensor1 = DigitalInputDevice(SENSOR_PIN1)
        self.sensor2 = DigitalInputDevice(SENSOR_PIN2)
        self.sensor3 = DigitalInputDevice(SENSOR_PIN3)
        self.sensor4 = DigitalInputDevice(SENSOR_PIN4)
        self.sensor5 = DigitalInputDevice(SENSOR_PIN5)
        self.sensor6 = DigitalInputDevice(SENSOR_PIN6)
        self.sensor7 = DigitalInputDevice(SENSOR_PIN7)
        self.sensor8 = DigitalInputDevice(SENSOR_PIN8)

    # センサの値を取得
    def get_sensor(self):
        traced = str(self.sensor1.value) + str(self.sensor2.value) + str(self.sensor3.value) + str(self.sensor4.value) + str(self.sensor5.value) + str(self.sensor6.value) + str(self.sensor7.value) + str(self.sensor8.value)
        return traced

    def get_sensor_test(self, cnt):
        line = ['00011000','00111100', 
                '11111110','01111100','00111000','00010000','11111100', 
                '01111000','00110000','11110000','01100000','11111000','01110000','00100000',
                '10000000','11000000','01000000','11100000',
                '00001000','00011100','00111110','01111111','00111111',
                '00000100','00001110','00011111','00000110','00001111','00001100','00011110',
                '00000010','00000111','00000011','00000001',
                '11111111','01111110']
        traced = line[cnt % len(line)]
        return traced

# ======================== #
# --- メイン実行ブロック --- #
# ======================== #
def main_loop():
    line = LineTrace()
    cnt = 0
    HLC = HighLevelCtrl()

    while True:
        try:
            traced_line = line.get_sensor_test(cnt)
            cnt += 1
            print(f"Traced line: {traced_line}")
            HLC.drive(traced_line)
            time.sleep(3)
        except KeyboardInterrupt:
            print("Program interrupted by user. Stopping motors.")
            break
        except Exception as e:
            print(f"Error during main loop: {e}")
            break

if __name__ == '__main__':
    main_loop()
