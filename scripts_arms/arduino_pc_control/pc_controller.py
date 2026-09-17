#!/usr/bin/env python3
"""
Keyboard-controlled robot arm for Adeept ADA031.
Real-time terminal UI with safety limits and visual feedback.
"""

import sys
import time
import threading
import serial
import serial.tools.list_ports

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("Warning: 'keyboard' module not installed. Run: pip install keyboard")
    print("Falling back to basic input mode (press Enter after each command).")

PORT = "COM1"
BAUD_RATE = 115200
DEFAULT_STEP = 5
MIN_STEP = 1
MAX_STEP = 45
SEND_THROTTLE_MS = 50
STATUS_POLL_INTERVAL = 2.0
CONNECT_RETRIES = 3
CONNECT_DELAY = 2.0

AXIS_NAMES = ["Base", "Shoulder", "Elbow", "Wrist", "Gripper"]
AXIS_MIN = 0
AXIS_MAX = 180
HOME_ANGLE = 90

KEY_MAP = {
    'a': (0, -1), 'd': (0, 1),
    'w': (1, 1), 's': (1, -1),
    'q': (2, -1), 'e': (2, 1),
    'r': (3, 1), 'f': (3, -1),
    'z': (4, -1), 'x': (4, 1),
}

class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BG_RED = '\033[101m'
    BG_GREEN = '\033[102m'

class RobotArmController:
    def __init__(self, port=PORT, baud=BAUD_RATE):
        self.port = port
        self.baud = baud
        self.ser = None
        self.running = False
        self.angles = [HOME_ANGLE] * 5
        self.target_angles = [HOME_ANGLE] * 5
        self.step = DEFAULT_STEP
        self.last_send_time = 0
        self.last_status_poll = 0
        self.connected = False
        self.connect_error = None
        self.lock = threading.Lock()
        self.key_listener = None

    def connect(self):
        for attempt in range(CONNECT_RETRIES):
            try:
                self.ser = serial.Serial(self.port, self.baud, timeout=0.1)
                time.sleep(2)
                self.ser.reset_input_buffer()
                self.connected = True
                self.connect_error = None
                self.send_home()
                return True
            except Exception as e:
                self.connect_error = str(e)
                if attempt < CONNECT_RETRIES - 1:
                    time.sleep(CONNECT_DELAY)
        return False

    def disconnect(self):
        self.running = False
        if self.ser and self.ser.is_open:
            try:
                self.send_home()
                time.sleep(0.5)
                self.ser.close()
            except:
                pass
        self.connected = False

    def clamp_angle(self, angle):
        return max(AXIS_MIN, min(AXIS_MAX, angle))

    def update_angle(self, axis, delta):
        with self.lock:
            new_angle = self.clamp_angle(self.target_angles[axis] + delta * self.step)
            if new_angle != self.target_angles[axis]:
                self.target_angles[axis] = new_angle
                return True
        return False

    def set_home(self):
        with self.lock:
            self.target_angles = [HOME_ANGLE] * 5
            self.angles = [HOME_ANGLE] * 5

    def send_home(self):
        self.send_command("HOME")

    def send_command(self, cmd):
        if self.ser and self.ser.is_open:
            try:
                self.ser.write((cmd + "\n").encode('utf-8'))
            except:
                self.connected = False

    def send_angles(self):
        now = time.time() * 1000
        if now - self.last_send_time < SEND_THROTTLE_MS:
            return
        with self.lock:
            if self.target_angles != self.angles:
                cmd = "M:" + ",".join(str(a) for a in self.target_angles)
                self.send_command(cmd)
                self.angles = self.target_angles.copy()
                self.last_send_time = now

    def poll_status(self):
        now = time.time()
        if now - self.last_status_poll > STATUS_POLL_INTERVAL:
            self.send_command("STATUS")
            self.last_status_poll = now

    def read_serial(self):
        if not self.ser or not self.ser.is_open:
            return
        try:
            while self.ser.in_waiting > 0:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith("POS:"):
                    parts = line[4:].split(',')
                    if len(parts) == 5:
                        with self.lock:
                            self.angles = [int(p) for p in parts]
                            self.target_angles = self.angles.copy()
                elif line == "OK":
                    pass
                elif line.startswith("ERROR"):
                    pass
        except:
            self.connected = False

    def adjust_step(self, delta):
        self.step = max(MIN_STEP, min(MAX_STEP, self.step + delta))

    def is_at_limit(self, axis):
        return self.target_angles[axis] <= AXIS_MIN or self.target_angles[axis] >= AXIS_MAX

    def on_key_event(self, event):
        if not self.running:
            return
        key = event.name.lower()
        if event.event_type == 'down':
            if key in KEY_MAP:
                axis, direction = KEY_MAP[key]
                if self.update_angle(axis, direction):
                    if self.is_at_limit(axis):
                        print('\a', end='', flush=True)
            elif key == 'h':
                self.set_home()
                self.send_home()
            elif key == '+' or key == '=':
                self.adjust_step(1)
            elif key == '-':
                self.adjust_step(-1)
            elif key == 'esc':
                self.running = False

    def start_keyboard_listener(self):
        if KEYBOARD_AVAILABLE:
            self.key_listener = keyboard.hook(self.on_key_event, suppress=True)
        else:
            self.key_listener = threading.Thread(target=self.basic_input_loop, daemon=True)
            self.key_listener.start()

    def basic_input_loop(self):
        print("\nBasic input mode. Enter commands (e.g., 'a' for Base-Left, 'h' for Home, 'q' to quit):")
        while self.running:
            try:
                cmd = input("> ").strip().lower()
                if not cmd:
                    continue
                if cmd == 'q' or cmd == 'quit' or cmd == 'exit':
                    self.running = False
                    break
                elif cmd == 'h':
                    self.set_home()
                    self.send_home()
                elif cmd == '+':
                    self.adjust_step(1)
                elif cmd == '-':
                    self.adjust_step(-1)
                elif cmd in KEY_MAP:
                    axis, direction = KEY_MAP[cmd]
                    self.update_angle(axis, direction)
                else:
                    print(f"Unknown: {cmd}. Keys: a/d,w/s,q/e,r/f,z/x, h, +/-, q")
            except (EOFError, KeyboardInterrupt):
                self.running = False
                break

    def stop_keyboard_listener(self):
        if KEYBOARD_AVAILABLE and self.key_listener:
            keyboard.unhook(self.key_listener)
        self.key_listener = None

    def render_bar(self, angle, axis_idx):
        width = 20
        filled = int((angle / AXIS_MAX) * width)
        bar = '█' * filled + '░' * (width - filled)
        pct = angle
        limit_str = ""
        if angle <= AXIS_MIN:
            limit_str = f" {Colors.RED}LIMIT ▼{Colors.RESET}"
        elif angle >= AXIS_MAX:
            limit_str = f" {Colors.RED}LIMIT ▲{Colors.RESET}"
        color = Colors.RED if (angle <= AXIS_MIN or angle >= AXIS_MAX) else Colors.GREEN
        return f"{color}{bar}{Colors.RESET} {pct:3d}°{limit_str}"

    def render_status_line(self):
        status_color = Colors.GREEN if self.connected else Colors.RED
        status_text = "● CONNECTED" if self.connected else f"○ DISCONNECTED ({self.connect_error})"
        return f"{Colors.CYAN}Port:{Colors.RESET} {self.port} @ {self.baud}  {status_color}{status_text}{Colors.RESET}"

    def render_help(self):
        return (
            f"{Colors.DIM}A/D{Colors.RESET}:Base  "
            f"{Colors.DIM}W/S{Colors.RESET}:Shoulder  "
            f"{Colors.DIM}Q/E{Colors.RESET}:Elbow  "
            f"{Colors.DIM}R/F{Colors.RESET}:Wrist  "
            f"{Colors.DIM}Z/X{Colors.RESET}:Gripper  "
            f"{Colors.DIM}H{Colors.RESET}:Home  "
            f"{Colors.DIM}+/-{Colors.RESET}:Step({self.step}°)  "
            f"{Colors.DIM}ESC{Colors.RESET}:Exit"
        )

    def clear_screen(self):
        print('\033[2J\033[H', end='')

    def hide_cursor(self):
        print('\033[?25l', end='')

    def show_cursor(self):
        print('\033[?25h', end='')

    def draw_ui(self):
        self.clear_screen()
        print(f"{Colors.BOLD}┌─ Robot Arm Controller ────────────────────┐{Colors.RESET}")
        print(f"│ {self.render_status_line():<42} │")
        print(f"│ {Colors.CYAN}Step:{Colors.RESET} {self.step}°  [+/- to change]{' ':<25} │")
        print(f"{Colors.BOLD}├─ Axes ────────────────────────────────────┤{Colors.RESET}")
        for i, name in enumerate(AXIS_NAMES):
            bar = self.render_bar(self.target_angles[i], i)
            print(f"│ {name:<9}: {bar:<35} │")
        print(f"{Colors.BOLD}├─ Commands ────────────────────────────────┤{Colors.RESET}")
        print(f"│ {self.render_help():<42} │")
        print(f"{Colors.BOLD}└───────────────────────────────────────────┘{Colors.RESET}")

    def run(self):
        print(f"Connecting to {self.port} @ {self.baud}...")
        if not self.connect():
            print(f"Failed to connect: {self.connect_error}")
            return

        self.running = True
        self.hide_cursor()
        self.start_keyboard_listener()

        try:
            last_draw = 0
            while self.running:
                self.read_serial()
                self.send_angles()
                self.poll_status()

                now = time.time()
                if now - last_draw > 0.05:
                    self.draw_ui()
                    last_draw = now

                time.sleep(0.01)

        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            self.stop_keyboard_listener()
            self.show_cursor()
            self.disconnect()
            print("\nDisconnected. Goodbye!")

def main():
    controller = RobotArmController()
    controller.run()

if __name__ == "__main__":
    main()