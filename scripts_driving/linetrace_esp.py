import _thread
import network
import select
import socket
import sys
import utime
from machine import Pin

# --- モーター1 (M1) 用 GPIO ピン定義 ---
# M1 CN1 Pin 7 (STEP) -> GPIO 19
# M1 CN1 Pin 6 (DIR)  -> GPIO 18
pin_step_m1 = Pin(19, Pin.OUT)
pin_dir_m1 = Pin(18, Pin.OUT)

# --- モーター2 (M2) 用 GPIO ピン定義 ---
# M2 CN1 Pin 7 (STEP) -> GPIO 17
# M2 CN1 Pin 6 (DIR)  -> GPIO 16
pin_step_m2 = Pin(17, Pin.OUT)
pin_dir_m2 = Pin(16, Pin.OUT)

# --- モーター状態・定量パラメータ管理変数 ---
m1_state = 0  # 1: 回転, 0: 停止
m1_dir = 1  # 1: 正転, 0: 逆転
m1_speed = 500  # パルス間隔 (µs) [初期周波数: 1.0 kHz]

m2_state = 0  # 1: 回転, 0: 停止
m2_dir = 1  # 1: 正転, 0: 逆転
m2_speed = 500  # パルス間隔 (µs) [初期周波数: 1.0 kHz]

# パルス生成タイマー保持変数 (µs)
m1_last_step = utime.ticks_us()
m2_last_step = utime.ticks_us()
m1_step_val = 0
m2_step_val = 0

# 初期出力状態の設定 (全ピン LOW 固定)
pin_step_m1.value(0)
pin_dir_m1.value(0)
pin_step_m2.value(0)
pin_dir_m2.value(0)


# --- Wi-Fi アクセスポイント (APモード) の初期化 ---
def start_ap():
    ap = network.WLAN(network.AP_IF)
    ap.active(True)
    ap.config(
        essid="ESP32-Motor-Control",
        authmode=network.AUTH_WPA2_PSK,
        password="password123",
    )
    print("AP Mode Started")
    print("IP Address:", ap.ifconfig()[0])


# --- 簡易DNSサーバー (キャプティブポータル用スレッド / UDP 53番ポート) ---
def dns_server_thread():
    udps = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udps.bind(("", 53))
    while True:
        try:
            data, addr = udps.recvfrom(1024)
            packet = (
                data[:2]
                + b"\x81\x80"
                + data[4:6]
                + data[4:6]
                + b"\x00\x00\x00\x00"
            )
            packet += data[12:]
            packet += b"\xc0\x0c"
            packet += b"\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04"
            packet += bytes([192, 168, 4, 1])
            udps.sendto(packet, addr)
        except Exception:
            pass


# --- モーター動作一括更新関数 (M2の回転方向論理を反転補正) ---
def update_motor_drive(s1, d1, sp1, s2, d2, sp2):
    global m1_state, m1_dir, m1_speed, m2_state, m2_dir, m2_speed
    m1_state, m1_dir, m1_speed = s1, d1, max(200, min(2000, sp1))
    m2_state, m2_dir, m2_speed = s2, d2, max(200, min(2000, sp2))

    # M1 は通常出力、M2 は物理取り付け向きに合わせて論理反転 (1 <-> 0)
    pin_dir_m1.value(1 if m1_dir > 0 else 0)
    pin_dir_m2.value(0 if m2_dir > 0 else 1)  # 反転処理 [ソース: TI DRV8825 Datasheet Section 8.3.1]


# --- シリアル文字列解析処理 ---
def parse_serial_command(cmd_str):
    try:
        data = cmd_str.strip().split(",")
        if len(data) == 6:
            update_motor_drive(
                int(data[0]),
                int(data[1]),
                int(data[2]),
                int(data[3]),
                int(data[4]),
                int(data[5]),
            )
            print("ACK Serial Command")
    except Exception as e:
        print("ERR Serial Parse:", e)


# --- HTML テンプレート ---
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ESP32 Dual Control Panel</title>
    <style>
        body { font-family: sans-serif; text-align: center; background: #181a1b; color: #fff; padding: 15px; margin: 0; }
        h1 { margin-bottom: 5px; color: #00d2ff; }
        p { font-size: 12px; color: #aaa; margin-top: 0; }
        .container { max-width: 380px; margin: 0 auto; background: #242729; padding: 20px; border-radius: 15px; box-shadow: 0 8px 16px rgba(0,0,0,0.5); box-sizing: border-box; }
        .dpad { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 15px 0; }
        .btn-rc { padding: 15px 0; font-size: 15px; font-weight: bold; color: white; background: #007bff; border: none; border-radius: 8px; cursor: pointer; user-select: none; }
        .btn-rc:active { background: #e63946; transform: scale(0.95); }
        .btn-stop { background: #d90429; }
        .btn-empty { visibility: hidden; }
        .guide-panel { background: #2f3336; padding: 12px; border-radius: 8px; margin-top: 15px; font-size: 13px; text-align: left; }
        .key-badge { background: #00d2ff; color: #000; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-family: monospace; }
        .speed-val { color: #00d2ff; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>ESP32 Control</h1>
        <p>WEBパネル (方向反転補正済)</p>

        <div class="dpad">
            <div class="btn-empty"></div>
            <button class="btn-rc" onclick="sendCmd('/cmd/forward')">▲ 前進 [W]</button>
            <div class="btn-empty"></div>

            <button class="btn-rc" onclick="sendCmd('/cmd/left')">◄ 左旋回 [A]</button>
            <button class="btn-rc btn-stop" onclick="sendCmd('/cmd/stop')">■ 停止 [Space]</button>
            <button class="btn-rc" onclick="sendCmd('/cmd/right')">右旋回 ► [D]</button>

            <div class="btn-empty"></div>
            <button class="btn-rc" onclick="sendCmd('/cmd/backward')">▼ 後退 [S]</button>
            <div class="btn-empty"></div>
        </div>

        <div class="dpad" style="grid-template-columns: 1fr 1fr; gap: 10px;">
            <button class="btn-rc" style="background:#2a9d8f;" onclick="sendCmd('/speed/up')">速度 UP (+100us) [I]</button>
            <button class="btn-rc" style="background:#e76f51;" onclick="sendCmd('/speed/down')">速度 DOWN (-100us) [K]</button>
        </div>

        <div class="guide-panel">
            <b>PC キーボード操作ガイド:</b><br>
            • <span class="key-badge">W</span>前進 / <span class="key-badge">S</span>後退 / <span class="key-badge">A</span>左旋回 / <span class="key-badge">D</span>右旋回<br>
            • <span class="key-badge">I</span> 速度UP / <span class="key-badge">K</span> 速度DOWN<br>
            • <span class="key-badge">Space</span> / <span class="key-badge">X</span> 即時停止<br>
            現在のパルス間隔: <span id="speed-disp" class="speed-val">500</span> µs
        </div>
    </div>

    <script>
        function sendCmd(path) {
            fetch(path).then(res => res.text()).then(val => {
                if(val && !isNaN(val)) document.getElementById('speed-disp').innerText = val;
            }).catch(e => console.log(e));
        }

        window.addEventListener('keydown', function(e) {
            if (e.repeat) return;
            const k = e.key.toLowerCase();
            if (k === 'w') sendCmd('/cmd/forward');
            else if (k === 's') sendCmd('/cmd/backward');
            else if (k === 'a') sendCmd('/cmd/left');
            else if (k === 'd') sendCmd('/cmd/right');
            else if (k === ' ') sendCmd('/cmd/stop');
            else if (k === 'x') sendCmd('/cmd/stop');
            else if (k === 'i') sendCmd('/speed/up');
            else if (k === 'k') sendCmd('/speed/down');
        });
    </script>
</body>
</html>
"""


# --- HTTP リクエスト処理 ---
def handle_http_client(conn):
    global m1_speed, m2_speed
    try:
        req = conn.recv(1024).decode("utf-8")
        if not req or len(req) == 0:
            conn.close()
            return

        if "GET /cmd/" in req or "GET /speed/" in req:
            if "GET /cmd/forward" in req:
                update_motor_drive(1, 1, m1_speed, 1, 1, m2_speed)
            elif "GET /cmd/backward" in req:
                update_motor_drive(1, 0, m1_speed, 1, 0, m2_speed)
            elif "GET /cmd/left" in req:
                update_motor_drive(1, 0, m1_speed, 1, 1, m2_speed)
            elif "GET /cmd/right" in req:
                update_motor_drive(1, 1, m1_speed, 1, 0, m2_speed)
            elif "GET /cmd/stop" in req:
                update_motor_drive(0, m1_dir, m1_speed, 0, m2_dir, m2_speed)
            elif "GET /speed/up" in req:
                new_sp = max(200, m1_speed - 100)
                update_motor_drive(
                    m1_state, m1_dir, new_sp, m2_state, m2_dir, new_sp
                )
            elif "GET /speed/down" in req:
                new_sp = min(2000, m1_speed + 100)
                update_motor_drive(
                    m1_state, m1_dir, new_sp, m2_state, m2_dir, new_sp
                )

            response = (
                "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\n"
                + str(m1_speed)
            )
            conn.send(response)
        else:
            response = (
                "HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=UTF-8\r\n\r\n"
                + HTML_TEMPLATE
            )
            conn.send(response)
    except Exception as e:
        print("HTTP Client Error:", e)
    finally:
        conn.close()


# --- メイン処理ループ ---
def main():
    global m1_last_step, m2_last_step, m1_step_val, m2_step_val
    start_ap()
    _thread.start_new_thread(dns_server_thread, ())

    http_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    http_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    http_sock.bind(("", 80))
    http_sock.listen(5)

    poller = select.poll()
    poller.register(sys.stdin, select.POLLIN)
    poller.register(http_sock, select.POLLIN)

    print("--- System Ready (WEB UI + WASD/IK + Serial) ---")

    while True:
        events = poller.poll(0)
        for obj, flag in events:
            if obj == sys.stdin:
                line = sys.stdin.readline()
                if line:
                    parse_serial_command(line)
            elif obj == http_sock:
                try:
                    conn, addr = http_sock.accept()
                    handle_http_client(conn)
                except Exception as e:
                    pass

        now = utime.ticks_us()

        if m1_state == 1:
            if utime.ticks_diff(now, m1_last_step) >= m1_speed:
                m1_last_step = now
                m1_step_val = 1 - m1_step_val
                pin_step_m1.value(m1_step_val)
        else:
            pin_step_m1.value(0)

        if m2_state == 1:
            if utime.ticks_diff(now, m2_last_step) >= m2_speed:
                m2_last_step = now
                m2_step_val = 1 - m2_step_val
                pin_step_m2.value(m2_step_val)
        else:
            pin_step_m2.value(0)


if __name__ == "__main__":
    main()
