import time
import board
import busio
from adafruit_pca9685 import PCA9685

PCA9685_ADDRESS = 0x40
SERVO_CHANNELS = [0, 1, 2, 3, 4, 5]
SERVO_FREQUENCY = 50
MIN_PULSE_US = 1000
MAX_PULSE_US = 2000
TEST_ANGLES = [90, 60, 90, 120, 90]

i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c, address=PCA9685_ADDRESS)
pca.frequency = SERVO_FREQUENCY

# 角度 → パルス幅 → PCA9685値
def angle_to_pulse_us(angle):
    # 安全のため角度を0～180に制限
    angle = max(0, min(180, angle))
    pulse_us = (MIN_PULSE_US + (MAX_PULSE_US - MIN_PULSE_US) * angle / 180)
    return pulse_us

def pulse_us_to_duty_cycle(pulse_us):
    # 50Hzの場合の1周期
    period_us = 1_000_000 / SERVO_FREQUENCY
    # 16bit PWM値へ変換
    duty = int(pulse_us / period_us * 65535)
    return duty

def set_servo_angle(channel, angle):
    pulse_us = angle_to_pulse_us(angle)
    duty = pulse_us_to_duty_cycle(pulse_us)
    pca.channels[channel].duty_cycle = duty
    print(f"CH{channel}: {angle:.1f} deg ({pulse_us:.0f} us)")

# サーボを停止
def stop_servo(channel):
    pca.channels[channel].duty_cycle = 0

# 全サーボを停止
def stop_all():
    for channel in SERVO_CHANNELS:
        stop_servo(channel)

# メイン
try:
    print("PCA9685 initialized.")
    print("Servo test start.")
    print()
    # まず全サーボを90度へ
    print("Set all servos to 90 degrees.")
    for channel in SERVO_CHANNELS:
        set_servo_angle(channel, 90)
        # 電流集中を避けるため少しずつ設定
        time.sleep(0.3)
    time.sleep(2)

    # 1軸ずつ動作確認
    for channel in SERVO_CHANNELS:
        print(f"\nTesting CH{channel}")
        # 60度
        set_servo_angle(channel, 60)
        time.sleep(1)
        # 120度
        set_servo_angle(channel, 120)
        time.sleep(1)
        # 90度
        set_servo_angle(channel, 90)
        time.sleep(1)
    print("\nTest completed.")
    # サーボ信号を停止
    stop_all()
except KeyboardInterrupt:
    print("\nInterrupted.")
finally:
    # 終了時にPWM停止
    stop_all()
    pca.deinit()
    print("PCA9685 deinitialized.")
