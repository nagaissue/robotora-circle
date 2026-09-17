import tkinter as tk
from tkinter import ttk, messagebox
from servo import myServo
from operate_servodb import DatabaseManager

##############################
# コントローラ画面の作成クラス #
##############################
class ServoController(tk.Tk):
    # コントローラ画面の初期化
    def __init__(self):
        super().__init__()
        # コントローラ画面の設定
        self.title("Servo Controller")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # 設定画面表示
        self.current_frame = None
        self.Transition("Setup")

    def Transition(self, display_name, gpio_values=None)->None:
        if self.current_frame:
            self.current_frame.destroy()
        frame = { "Setup": Setup(self), "Controller": Controller(self, gpio_values) }
        self.current_frame = frame[display_name]
        self.current_frame.grid(row=0, column=0, sticky="nsew")
        self.current_frame.tkraise()

#################
# 設定画面クラス #
#################
class Setup(tk.Frame):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.axis_gpio = [12, 13, 18, 19, 20, 21]  # デフォルトのGPIO番号
        self.axis_labels = []
        self.axis_entries = []
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self.create_title()
        self.create_setup()

    def create_title(self):
        # タイトルの作成
        self.title_frame = tk.Frame(self, bg="#ffffff")
        self.title_frame.grid(row=0, column=0, sticky="nsew")
        self.title_label = tk.Label(self.title_frame, text="設定画面", bg="#92fbb8", font=("Yu Gothic UI", 24, "bold"))
        self.title_label.pack(fill=tk.BOTH, expand=True)

        self.title_frame.rowconfigure(0, weight=1)
        self.title_frame.columnconfigure(0, weight=1)

    def create_setup(self):
        # コントローラフレームの作成
        self.setup_frame = tk.Frame(self, bg="#92fbb8")
        self.setup_frame.grid(row=1, column=0, sticky="nsew")

        # コントローラフレームの内容の作成
        tk.Label(self.setup_frame, text="軸数", font=("", 18, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        self.select = ttk.Combobox(self.setup_frame, values=["1軸", "2軸", "3軸", "4軸", "5軸", "6軸"], state="readonly", font=("", 18), justify="center")
        self.select.bind("<<ComboboxSelected>>", self.getCondition)
        self.select.set("5軸")
        self.select.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        # GPIO番号入力欄の作成
        self.create_gpio_entry(5)

        # 設定完了ボタンの作成
        tk.Button(self.setup_frame, text="設定完了", command=self.transition_to_controller, font=("Yu Gothic UI", 18, "bold"), bg="#f6f86a").grid(row=7, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        # コントローラフレームの行と列の重みを設定
        self.setup_frame.columnconfigure(0, weight=1)
        self.setup_frame.columnconfigure(1, weight=1)

    def getCondition(self, event)->None:
        selected = self.select.get()

        # 既存のラベルとエントリを削除
        for i in range(len(self.axis_labels)):
            self.axis_labels[i].destroy()
        for i in range(len(self.axis_entries)):
            self.axis_entries[i].destroy()
        self.axis_labels.clear()
        self.axis_entries.clear()

        # 選択された軸数に応じてGPIO番号入力欄を作成
        try:
            axis_number = int(selected[0])  # 選択された軸数を取得
            self.create_gpio_entry(axis_number)
        except ValueError:
            messagebox.showerror("入力エラー", "有効な軸数を入力してください。")

    def create_gpio_entry(self, axis_number):
        for i in range(1, axis_number + 1):
            label = tk.Label(self.setup_frame, text=f"axis{i}：GPIO", font=("Yu Gothic UI", 18, "bold"))
            label.grid(row=i, column=0, padx=5, pady=5, sticky="nsew")
            self.axis_labels.append(label)

            entry = tk.Entry(self.setup_frame, font=("Yu Gothic UI", 18), justify="center")
            entry.insert(0, str(self.axis_gpio[i-1]))
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="nsew")
            self.axis_entries.append(entry)

    def get_gpio_values(self):
        gpio_values = []
        print("axis_entries:", len(self.axis_entries))
        for i in range(len(self.axis_entries)):
            value = self.axis_entries[i].get()
            if value.isdigit():
                gpio_values.append(int(value))
            else:
                messagebox.showerror("入力エラー", "GPIO番号は整数で入力してください。")
                return None
        return gpio_values

    def transition_to_controller(self):
        gpio_values = self.get_gpio_values()
        if gpio_values is not None:
            self.parent.Transition("Controller", gpio_values=gpio_values)

########################
# コントローラ画面クラス #
########################
class Controller(tk.Frame):
    def __init__(self, parent, gpio_values=None):
        super().__init__()
        self.parent = parent
        self.axis_number = len(gpio_values) if gpio_values else 0
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        self.servo = [myServo(int(gpio)) for gpio in gpio_values] if gpio_values else []
        self.db_manager = DatabaseManager(axis_number=self.axis_number) if gpio_values else None

        self.create_title()
        self.create_treeview()
        self.create_controller()

    def create_title(self):
        # タイトルの作成
        self.title_frame = tk.Frame(self, bg="#ffffff")
        self.title_frame.grid(row=0, column=0, sticky="nsew")
        self.title_label = tk.Label(self.title_frame, text="コントローラー画面", bg="#92fbb8", font=("Yu Gothic UI", 24, "bold"))
        self.title_label.pack(fill=tk.BOTH, expand=True)

        self.title_frame.rowconfigure(0, weight=1)
        self.title_frame.columnconfigure(0, weight=1)

    # データ表示用のtreeview作成
    def create_treeview(self):
        # データ表示用のフレームの作成
        self.view_frame = tk.Frame(self, bg="#ffffff")
        self.view_frame.grid(row=1, column=0, sticky="nsew")
        self.view_frame.rowconfigure(0, weight=1)
        self.view_frame.columnconfigure(0, weight=1)
        # treeviewのスタイル設定
        ttk.Style().configure("Treeview", font=("Yu Gothic UI", 18, "bold"), rowheight=30)
        ttk.Style().configure("Treeview.Heading", font=("Yu Gothic UI", 16, "bold"))
        # treeviewの作成
        self.treeview_columns = ["id"] + [f"axis{i+1}" for i in range(self.axis_number)]
        self.treeview_headings = ["ID"] + [f"サーボ{i+1}軸" for i in range(self.axis_number)]
        self.treeview = ttk.Treeview(self.view_frame, columns=tuple(self.treeview_columns), show="headings")
        self.treeview.grid(row=0, column=0, sticky="nsew")
        self.treeview.heading("id", text="ID")
        for i in range(self.axis_number):
            self.treeview.heading(self.treeview_columns[i+1], text=self.treeview_headings[i+1], anchor=tk.CENTER)
        self.treeview.column("id", width=50, stretch=tk.YES)
        for i in range(self.axis_number):
            self.treeview.column(self.treeview_columns[i+1], width=80, stretch=tk.YES)
        # TreeViewの高さを調整
        self.treeview["height"] = 10
        # データベースからデータを取得してtreeviewに表示
        self.refresh_data()

    # データベースからデータを取得してtreeviewに表示
    def refresh_data(self):
        # treeviewの内容をクリア
        for row in self.treeview.get_children():
            self.treeview.delete(row)
        # データベースからデータを取得
        data = self.db_manager.select_all_data() if self.db_manager else []
        # データをtreeviewに挿入
        for row in data:
            self.treeview.insert("", "end", values=row)

    # コントローラフレームの作成
    def create_controller(self):
        # コントローラフレームの作成
        self.controller_frame = tk.Frame(self, bg="#92fbb8")
        self.controller_frame.grid(row=2, column=0, sticky="nsew")
        # コントローラフレームの内容の作成
        self.labels = []
        self.create_lables()
        # コントローラフレームの内容を更新
        self.update_labels()
        # サーボの角度を調整するスケールの作成
        self.scales = []
        self.create_scales()
        # サーボの角度を制御するボタンとデータベース操作のボタンの作成
        tk.Button(self.controller_frame, text="角度適用", command=self.control_arm, font=("Yu Gothic UI", 18, "bold"), bg="#f6f86a").grid(row=2, column=0, padx=5, sticky="ew")
        tk.Button(self.controller_frame, text="状態保存", command=self.save_state, font=("Yu Gothic UI", 18, "bold"), bg="#66e66d").grid(row=2, column=1, padx=5, sticky="ew")
        tk.Button(self.controller_frame, text="状態上書き", command=self.overwrite_state, font=("Yu Gothic UI", 18, "bold"), bg="#54fd62").grid(row=2, column=2, padx=5, sticky="ew")
        tk.Button(self.controller_frame, text="状態削除", command=self.delete_state, font=("Yu Gothic UI", 18, "bold"), bg="#ffa565").grid(row=2, column=3, padx=5, sticky="ew")
        tk.Button(self.controller_frame, text="全状態削除", command=self.delete_all_states, font=("Yu Gothic UI", 18, "bold"), bg="#f09952").grid(row=2, column=4, padx=5, sticky="ew")
        tk.Button(self.controller_frame, text="すべて実行", command=self.execute_all_states, font=("Yu Gothic UI", 18, "bold"), bg="#f6f86a").grid(row=3, column=0, columnspan=5, padx=5, pady=5, sticky="ew")
        # コントローラフレームの行と列の重みを設定
        self.controller_frame.rowconfigure(0, weight=1)
        self.controller_frame.rowconfigure(1, weight=1)
        self.controller_frame.rowconfigure(2, weight=1)
        self.controller_frame.columnconfigure(0, weight=1)
        self.controller_frame.columnconfigure(1, weight=1)
        self.controller_frame.columnconfigure(2, weight=1)
        self.controller_frame.columnconfigure(3, weight=1)
        self.controller_frame.columnconfigure(4, weight=1)

    def create_lables(self):
        for i in range(self.axis_number):
            label = tk.Label(self.controller_frame, text=f"angle{i+1}：0", bg="#92fbb8", font=("Yu Gothic UI", 18, "bold"))
            label.grid(row=0, column=i, padx=5)
            self.labels.append(label)

    # サーボの現在の状態をラベルに表示する関数
    def update_labels(self):
        for i in range(self.axis_number):
            angle = self.servo[i].get_current_angle()
            self.labels[i].config(text=f"angle{i+1}：{angle}")

    # サーボの角度を調整するスケールの作成
    def create_scales(self):
        for i in range(self.axis_number):
            min, max = self.servo[i].get_angle_range()
            scale = tk.Scale(self.controller_frame, from_=min, to=max, resolution=self.servo[i].get_min_rotation_angle(), orient=tk.HORIZONTAL, bg="#9c7fd1", font=("Yu Gothic UI", 14))
            scale.grid(row=1, column=i, padx=5, pady=5, ipadx=20)
            self.scales.append(scale)

    # サーボの角度を制御する関数
    def control_arm(self):
        for i in range(self.axis_number):
            angle = self.scales[i].get()
            self.servo[i].set_angle(int(angle))
        self.update_labels()

    # データベースに保存された状態をすべて実行する関数
    def execute_all_states(self):
        data = self.db_manager.select_all_data()
        for row in data:
            print(f"{row[0]} : [{', '.join(str(angle) for angle in row[1:])}]")
            for i in range(1, len(row)):
                self.servo[i-1].set_angle(int(row[i]))
            self.after(1000)  # 状態を切り替える間隔を1秒に設定

    # 現在の状態をデータベースに保存する関数
    def save_state(self):
        angle = []
        for i in range(self.axis_number):
            if self.servo[i].get_current_angle() < 0:
                messagebox.showwarning("保存エラー", f"サーボ{i+1}の角度が負の値です。保存できません。")
                return        
            angle.append(0 if self.servo[i].get_current_angle() < 0 else self.servo[i].get_current_angle())
        self.db_manager.insert_data(axis_angle=tuple(angle))
        self.refresh_data()

    # 選択した状態をデータベースに上書き保存する関数
    def overwrite_state(self):
        selected_item = self.treeview.selection()
        if not selected_item:
            messagebox.showwarning("選択エラー", "上書き保存する状態を選択してください。")
            return
        data_id = self.treeview.item(selected_item)["values"][0]
        angle = []
        for i in range(self.axis_number):
            angle.append(0 if self.servo[i].get_current_angle() < 0 else self.servo[i].get_current_angle())
        self.db_manager.update_data(data_id=data_id, axis_angle=tuple(angle))
        self.refresh_data()

    # 選択した状態をデータベースから削除する関数
    def delete_state(self):
        selected_item = self.treeview.selection()
        if not selected_item:
            messagebox.showwarning("選択エラー", "削除する状態を選択してください。")
            return
        data_id = self.treeview.item(selected_item)["values"][0]
        self.db_manager.delete_data(data_id)
        self.refresh_data()

    # データベースから全ての状態を削除する関数
    def delete_all_states(self):
        self.db_manager.delete_all_data()
        self.refresh_data()


if __name__ == "__main__":
    app = ServoController()
    app.mainloop()
