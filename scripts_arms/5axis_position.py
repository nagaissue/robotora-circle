import math
import tkinter as tk
from tkinter import ttk, messagebox


class FiveAxisArmGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("5軸ロボットアーム 逆運動学")
        self.root.geometry("900x700")

        # 目標座標
        frame_target = ttk.LabelFrame(root, text="目標座標")
        frame_target.pack(fill="x", padx=10, pady=10)
        self.x_entry = self.create_entry(frame_target, "X座標 (mm)", 0, 0, "180")
        self.y_entry = self.create_entry(frame_target, "Y座標 (mm)", 0, 2, "50")
        self.z_entry = self.create_entry(frame_target, "Z座標 (mm)", 0, 4, "120")
        self.wrist_entry = self.create_entry(frame_target, "手首角度 (°)", 1, 0, "0")
        self.gripper_entry = self.create_entry(frame_target, "グリッパ角度 (°)", 1, 2, "90")

        # アーム寸法
        frame_dim = ttk.LabelFrame(root, text="アーム寸法")
        frame_dim.pack(fill="x", padx=10, pady=5)
        self.base_height_entry = self.create_entry(frame_dim, "基部高さ", 0, 0, "60")
        self.link1_entry = self.create_entry(frame_dim, "第1リンク長", 0, 2, "105")
        self.link2_entry = self.create_entry(frame_dim, "第2リンク長", 0, 4, "100")
        self.tool_entry = self.create_entry(frame_dim, "手先長", 1, 0, "70")

        # サーボ設定
        frame_servo = ttk.LabelFrame(root, text="サーボ設定")
        frame_servo.pack(fill="x", padx=10, pady=5)
        self.offset_entries = []
        self.direction_entries = []
        self.create_servo_rows(frame_servo)

        ttk.Button(root, text="計算", command=self.calculate).pack(pady=10)

        frame_result = ttk.LabelFrame(root, text="計算結果")
        frame_result.pack(fill="both", expand=True, padx=10, pady=5)
        self.result_text = tk.Text(frame_result, height=12, font=("Consolas", 12))
        self.result_text.pack(fill="both", expand=True, padx=5, pady=5)

    def create_entry(self, parent, label, row, column, default):
        ttk.Label(parent, text=label).grid(row=row, column=column, padx=5, pady=5)
        entry = ttk.Entry(parent, width=12)
        entry.insert(0, default)
        entry.grid(row=row, column=column + 1, padx=5, pady=5)
        return entry

    def create_servo_rows(self, parent):
        headers = ["軸", "オフセット", "方向"]
        for col, text in enumerate(headers):
            ttk.Label(parent, text=text).grid(row=0, column=col, padx=8, pady=5)

        roles = ["基準", "肩", "肘", "手首", "グリッパ"]
        for i, role in enumerate(roles):
            ttk.Label(parent, text=f"{role}").grid(row=i + 1, column=0, padx=8, pady=4)
            offset = ttk.Entry(parent, width=8)
            offset.insert(0, "90")
            offset.grid(row=i + 1, column=1, padx=8, pady=4)
            direction = ttk.Combobox(parent, values=["1", "-1"], width=6, state="readonly")
            direction.set("1")
            direction.grid(row=i + 1, column=2, padx=8, pady=4)
            self.offset_entries.append(offset)
            self.direction_entries.append(direction)

    def inverse_kinematics(self, x, y, z, wrist_pitch, base_height, link1, link2, tool, gripper_angle):
        wrist_pitch_rad = math.radians(wrist_pitch)
        base = math.atan2(y, x)
        r = math.sqrt(x * x + y * y)
        wx = r - tool * math.cos(wrist_pitch_rad)
        wz = (z - base_height - tool * math.sin(wrist_pitch_rad))
        d = math.sqrt(wx * wx + wz * wz)

        if d > link1 + link2:
            raise ValueError("目標位置が可動範囲外です")
        if d < abs(link1 - link2):
            raise ValueError("目標位置が可動範囲外です")

        cos_elbow = (wx * wx + wz * wz - link1 * link1 - link2 * link2) / (2 * link1 * link2)
        cos_elbow = max(-1.0, min(1.0, cos_elbow))
        elbow = math.acos(cos_elbow)
        shoulder = math.atan2(wz, wx) - math.atan2(link2 * math.sin(elbow), link1 + link2 * math.cos(elbow))
        wrist = wrist_pitch_rad - shoulder - elbow

        raw_angles = [base, shoulder, elbow, wrist, math.radians(gripper_angle)]
        result = []
        for i, angle_rad in enumerate(raw_angles):
            angle = math.degrees(angle_rad)
            offset = float(self.offset_entries[i].get())
            direction = int(self.direction_entries[i].get())
            angle = angle * direction + offset
            angle = int(round(angle))
            angle = max(0, min(180, angle))
            result.append(angle)
        return result

    def calculate(self):
        try:
            x = float(self.x_entry.get())
            y = float(self.y_entry.get())
            z = float(self.z_entry.get())
            wrist_pitch = float(self.wrist_entry.get())
            gripper_angle = float(self.gripper_entry.get())
            base_height = float(self.base_height_entry.get())
            link1 = float(self.link1_entry.get())
            link2 = float(self.link2_entry.get())
            tool = float(self.tool_entry.get())

            angles = self.inverse_kinematics(
                x, y, z, wrist_pitch, base_height, link1, link2, tool, gripper_angle
            )

            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, "===== 計算結果 =====\n\n")
            roles = ["基準", "肩", "肘", "手首", "グリッパ"]
            for role, angle in zip(roles, angles):
                self.result_text.insert(tk.END, f"{role}: {angle}°\n")
        except ValueError as e:
            messagebox.showerror("計算エラー", str(e))
        except Exception as e:
            messagebox.showerror("エラー", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = FiveAxisArmGUI(root)
    root.mainloop()
