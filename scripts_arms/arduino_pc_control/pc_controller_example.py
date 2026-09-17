import serial
import serial.tools.list_ports
import time

def find_arduino_port():
    # COM5に直接固定して接続
    return "COM5"

def main():
    port = find_arduino_port()
    if not port:
        print("Error: No COM port found. Please connect your Arduino.")
        return

    baud_rate = 115200
    print(f"Connecting to {port} at {baud_rate} baud...")

    try:
        ser = serial.Serial(port, baud_rate, timeout=1)
        time.sleep(2) # Arduinoのリセット待機
        
        # 接続確認メッセージの読み取り
        while ser.in_waiting > 0:
            line = ser.readline().decode('utf-8').strip()
            print(f"RX: {line}")

        # 例1: ホームポジション（全て90度）へ移動
        print("Sending command: HOME")
        ser.write(b"HOME\n")
        time.sleep(1)
        print(ser.readline().decode('utf-8').strip())

        # 例2: 各サーボの角度を指定して動かす (Base, Shoulder, Elbow, Wrist, Gripper)
        # 形式: M:base,shoulder,elbow,wrist,gripper (0〜180度)
        angles = "M:90,45,135,90,30"
        print(f"Sending command: {angles}")
        ser.write((angles + "\n").encode('utf-8'))
        time.sleep(1)
        print(ser.readline().decode('utf-8').strip())

        # 例3: ステータス取得
        print("Sending command: STATUS")
        ser.write(b"STATUS\n")
        time.sleep(0.5)
        print(ser.readline().decode('utf-8').strip())

        ser.close()
        print("Connection closed.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
