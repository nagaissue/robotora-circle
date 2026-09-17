import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import time

class ADA031ControllerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Adeept ADA031 Teaching & Playback Controller")
        self.root.geometry("550x650")
        self.root.resizable(False, False)

        self.ser = None
        self.is_connected = False

        self.create_widgets()

    def create_widgets(self):
        # --- Connection Frame ---
        conn_frame = ttk.LabelFrame(self.root, text=" Serial Connection ", padding=10)
        conn_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(conn_frame, text="Port:").grid(row=0, column=0, sticky="w", padx=5)
        
        self.port_combo = ttk.Combobox(conn_frame, width=15, state="readonly")
        self.port_combo.grid(row=0, column=1, padx=5)
        self.update_ports()

        ttk.Button(conn_frame, text="Refresh", command=self.update_ports).grid(row=0, column=2, padx=5)

        ttk.Label(conn_frame, text="Baud:").grid(row=0, column=3, sticky="w", padx=5)
        self.baud_combo = ttk.Combobox(conn_frame, width=8, values=["9600", "115200"], state="readonly")
        self.baud_combo.set("9600")
        self.baud_combo.grid(row=0, column=4, padx=5)

        self.conn_btn = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.conn_btn.grid(row=0, column=5, padx=10)

        # --- Servos Control Frame ---
        servo_frame = ttk.LabelFrame(self.root, text=" Servo Angle Sliders (0 - 180 deg) ", padding=15)
        servo_frame.pack(fill="x", padx=10, pady=10)

        self.servo_names = ["1: Base", "2: Shoulder", "3: Elbow", "4: Wrist", "5: Gripper"]
        self.sliders = []
        self.val_labels = []

        for i, name in enumerate(self.servo_names):
            lbl = ttk.Label(servo_frame, text=name, width=12)
            lbl.grid(row=i, column=0, sticky="w", pady=8)

            slider = ttk.Scale(servo_frame, from_=0, to=180, orient="horizontal", length=250, command=lambda v, idx=i: self.on_slider_move(idx))
            slider.set(90)
            slider.grid(row=i, column=1, padx=10, pady=8)
            self.sliders.append(slider)

            val_lbl = ttk.Label(servo_frame, text="90", width=4)
            val_lbl.grid(row=i, column=2, padx=5, pady=8)
            self.val_labels.append(val_lbl)

        # --- Teaching & Playback Control Frame ---
        control_frame = ttk.LabelFrame(self.root, text=" Teaching & Playback Control ", padding=15)
        control_frame.pack(fill="x", padx=10, pady=10)

        btn_style = {'width': 18, 'padding': 8}
        
        self.btn_save = ttk.Button(control_frame, text="Current Pose Save", command=self.save_pose, **btn_style)
        self.btn_save.grid(row=0, column=0, padx=10, pady=5)

        self.btn_play = ttk.Button(control_frame, text="Play Sequence", command=self.play_sequence, **btn_style)
        self.btn_play.grid(row=0, column=1, padx=10, pady=5)

        self.btn_reset = ttk.Button(control_frame, text="Clear EEPROM", command=self.reset_eeprom, **btn_style)
        self.btn_reset.grid(row=1, column=0, padx=10, pady=10)

        self.btn_status = ttk.Button(control_frame, text="Get Status", command=self.get_status, **btn_style)
        self.btn_status.grid(row=1, column=1, padx=10, pady=10)

        # --- Log / Status Output Frame ---
        log_frame = ttk.LabelFrame(self.root, text=" Log / Console ", padding=10)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.log_box = tk.Text(log_frame, height=8, state="disabled", bg="#1e1e1e", fg="#00ff00", font=("Consolas", 9))
        self.log_box.pack(fill="both", expand=True, side="left")

        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_box.yview)
        scrollbar.pack(fill="y", side="right")
        self.log_box.configure(yscrollcommand=scrollbar.set)

    def log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"{message}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def update_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.set(ports[0])
        else:
            self.port_combo.set("")

    def toggle_connection(self):
        if not self.is_connected:
            port = self.port_combo.get()
            baud = int(self.baud_combo.get())
            if not port:
                messagebox.showerror("Error", "Please select a COM port.")
                return
            try:
                self.ser = serial.Serial(port, baud, timeout=1)
                time.sleep(2) # Wait for Arduino reset
                self.is_connected = True
                self.conn_btn.text = "Disconnect"
                self.conn_btn.configure(text="Disconnect")
                self.log(f"Connected to {port} at {baud} baud.")
                self.get_status()
            except Exception as e:
                messagebox.showerror("Connection Error", str(e))
        else:
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.is_connected = False
            self.conn_btn.configure(text="Connect")
            self.log("Disconnected.")

    def send_command(self, cmd):
        if not self.is_connected or not self.ser:
            messagebox.showwarning("Warning", "Not connected to Arduino.")
            return None
        try:
            full_cmd = f"{cmd}\n"
            self.ser.write(full_cmd.encode('utf-8'))
            self.log(f"TX: {cmd}")
            time.sleep(0.05)
            
            response = self.ser.readline().decode('utf-8').strip()
            if response:
                self.log(f"RX: {response}")
            return response
        except Exception as e:
            self.log(f"Error: {e}")
            return None

    def on_slider_move(self, idx):
        val = int(self.sliders[idx].get())
        self.val_labels[idx].configure(text=str(val))
        
        # Build move command
        angles = [int(s.get()) for s in self.sliders]
        cmd = f"M:{angles[0]},{angles[1]},{angles[2]},{angles[3]},{angles[4]}"
        self.send_command(cmd)

    def save_pose(self):
        self.send_command("SAVE")

    def play_sequence(self):
        self.log("Playing sequence...")
        self.send_command("PLAY")

    def reset_eeprom(self):
        if messagebox.askyesno("Confirmation", "Are you sure you want to clear all saved poses in EEPROM?"):
            self.send_command("RESET")

    def get_status(self):
        self.send_command("STATUS")

if __name__ == "__main__":
    root = tk.Tk()
    app = ADA031ControllerApp(root)
    root.mainloop()
