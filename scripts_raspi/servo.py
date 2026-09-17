from time import sleep

try:
    from gpiozero import AngularServo, DigitalOutputDevice
    library = True
except Exception as e:
    library = False

library = False

if library:
    ########################
    # サーボモータ制御クラス #
    ########################
    class myServo:
        # 初期化関数
        def __init__(self, gpio_pin=18, correction=0.0):
            self.myGPIO = gpio_pin
            self.SERVO_DELAY_SEC = 0.001 
            self.myCorrection = correction
            self.maxPW = (2.5 + self.myCorrection) / 1000
            self.minPW = (0.5 - self.myCorrection) / 1000
            self.servo = AngularServo(self.myGPIO, initial_angle=0, min_angle=0, max_angle=180, min_pulse_width=self.minPW, max_pulse_width=self.maxPW)

        # 角度範囲取得
        def get_angle_range(self):
            self.set_angle(0)
            min_angle = self.get_current_angle()
            self.servo.min_angle = min_angle
            self.set_angle(180)
            max_angle = self.get_current_angle()
            self.servo.max_angle = max_angle
            return min_angle, max_angle

        # 最小回転角度幅取得
        def get_min_rotation_angle(self):
            self.servo.angle = 0  # まず0度に設定
            sleep(self.SERVO_DELAY_SEC)  # サーボが動くのを待つ
            current_angle = self.get_current_angle()
            next_angle = current_angle
            set_angle = 0
            while next_angle == current_angle:
                set_angle += 1
                self.servo.angle = set_angle  # 1度回転させる
                sleep(self.SERVO_DELAY_SEC)  # サーボが動くのを待つ
                next_angle = self.get_current_angle()
            return abs(next_angle - current_angle)
        
        # 現在の角度取得
        def get_current_angle(self):
            return self.servo.angle

        # 動作確認用関数
        def check_servo(self):
            for i in range(3):
                for angle in range(0, 181, 1):   # make servo rotate from 0 to 180 deg
                    self.set_angle(angle)
                sleep(0.5)
                for angle in range(180, -1, -1): # make servo rotate from 180 to 0 deg
                    self.set_angle(angle)
                sleep(0.5)

        # サーボモータ制御関数
        def set_angle(self, angle=0):
            if angle < 0:
                angle = self.servo.min_angle
            elif angle > 180:
                angle = self.servo.max_angle

            step = self.get_min_rotation_angle()
            moving = True
            while moving:
                moving = False
                current_angle = self.get_current_angle()
                if abs(angle - current_angle) > step:
                    if angle > current_angle:
                        self.servo.angle = current_angle + step
                    else:
                        self.servo.angle = current_angle - step
                    moving = True
                else:
                    self.servo.angle = angle  # 最終的に目標角度に設定
                sleep(self.SERVO_DELAY_SEC)
else:
    ########################
    # サーボモータ制御クラス #
    ########################
    class myServo:
        def __init__(self, gpio_pin):
            self.angle = 0

        def get_angle_range(self):
            return -9, 171

        def get_min_rotation_angle(self):
            return 18

        def get_current_angle(self):
            return self.angle

        def check_servo(self):
            print("Servo check function called")

        def set_angle(self, angle=0):
            if angle < 0:
                self.angle = -9
            elif angle > 180:
                self.angle = 171
            else:
                min, _ = self.get_angle_range()
                rotate = self.get_min_rotation_angle()
                num = 0
                while angle > min + num * rotate:
                    num += 1
                self.angle = min + num * rotate
