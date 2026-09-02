import threading
import tkinter as tk

# 引数が渡されなかったことを判定するためのセンチネルオブジェクト
_UNSPECIFIED = object()

class OverlayState:
    def __init__(self):
        self.lock = threading.Lock()
        self.data = {
            "status": "データを取得中...",
            "strongest_champion": None,
        }

    def update(self, *, status=_UNSPECIFIED, strongest_champion=_UNSPECIFIED):
        with self.lock:
            if status is not _UNSPECIFIED:
                self.data["status"] = status
            if strongest_champion is not _UNSPECIFIED:
                self.data["strongest_champion"] = strongest_champion

    def snapshot(self):
        with self.lock:
            return dict(self.data)


class OverlayWindow:
    def __init__(self, state):
        self.state = state
        self._closed = False
        self.root = tk.Tk()
        self.root.title("LoL OP Checker")
        
        # 枠なし、常に最前面
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)

        # 画面左上に配置 (幅 270px, 高さ 80px, x=10, y=10)
        self.root.geometry("270x80+10+10")
        
        # 近未来的なディープダーク背景
        self.root.configure(bg="#080c12")

        self._drag_start = None

        # グラスモフィズムを意識した境界線つきのフレーム
        self.frame = tk.Frame(
            self.root,
            bg="#080c12",
            highlightbackground="#1f2633",
            highlightthickness=1,
        )
        self.frame.pack(fill="both", expand=True)

        # ヘッダー領域（タイトル＋閉じるボタン）
        self.header_frame = tk.Frame(self.frame, bg="#080c12")
        self.header_frame.pack(fill="x", padx=4, pady=(2, 0))

        # タイトル表示
        self.title_label = tk.Label(
            self.header_frame,
            text="MOST POWERFUL CHAMPION",
            anchor="w",
            bg="#080c12",
            fg="#ff4655", # 警告色っぽい鮮やかなネオンレッド
            font=("Meiryo UI", 9, "bold"),
            padx=4,
            pady=2,
        )
        self.title_label.pack(side="left", fill="x", expand=True)

        # 閉じるボタン（視認性が高く押しやすい✕ボタン、ホバー時に赤く変化）
        self.close_button = tk.Button(
            self.header_frame,
            text="✕",
            command=self.close,
            bg="#080c12",
            fg="#94a3b8",
            activebackground="#dc2626",
            activeforeground="#ffffff",
            bd=0,
            highlightthickness=0,
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 9, "bold"),
            width=3,
            height=1,
        )
        self.close_button.pack(side="right", padx=(0, 2), pady=0)

        # 閉じるボタンのホバーエフェクト
        self.close_button.bind("<Enter>", lambda _: self.close_button.config(bg="#ef4444", fg="#ffffff"))
        self.close_button.bind("<Leave>", lambda _: self.close_button.config(bg="#080c12", fg="#94a3b8"))

        # チャンピオン情報表示用ラベル
        self.info_label = tk.Label(
            self.frame,
            text="Loading...",
            justify="left",
            anchor="nw",
            bg="#0d131f",
            fg="#e2e8f0",
            font=("Meiryo UI", 10),
            padx=8,
            pady=6,
        )
        self.info_label.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        # 棒グラフ描画用キャンバス
        self.canvas = tk.Canvas(
            self.frame,
            bg="#0d131f",
            highlightthickness=0,
            bd=0,
        )

        # ドラッグ可能にするためのバインド（閉じるボタンはクリックを優先するため除外）
        for widget in (self.root, self.frame, self.header_frame, self.title_label, self.info_label, self.canvas):
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._drag)

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.refresh_view()

    def is_closed(self):
        return self._closed or self.root is None

    def _widget_exists(self, widget):
        if widget is None:
            return False
        try:
            return bool(widget.winfo_exists())
        except tk.TclError:
            return False

    def _start_drag(self, event):
        self._drag_start = (event.x_root, event.y_root)

    def _drag(self, event):
        if not self._drag_start:
            return
        x_root, y_root = self._drag_start
        dx = event.x_root - x_root
        dy = event.y_root - y_root
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")
        self._drag_start = (event.x_root, event.y_root)

    def refresh_view(self):
        if self.is_closed() or not self._widget_exists(self.info_label):
            return

        snapshot = self.state.snapshot()
        champ = snapshot.get("strongest_champion")
        status = snapshot.get("status")

        if champ:
            name = champ.get("name", "-")
            kills = champ.get("kills", 0)
            deaths = champ.get("deaths", 0)
            assists = champ.get("assists", 0)
            is_dead = champ.get("is_dead", False)
            level = champ.get("level", 1)
            
            gold_ratio = champ.get("gold_ratio", 1.0)
            my_gold_ratio = champ.get("my_gold_ratio", 1.0)
            
            avg_pct = 100
            my_pct = int(round(my_gold_ratio * 100))
            enemy_pct = int(round(gold_ratio * 100))

            if is_dead:
                respawn_timer = champ.get("respawn_timer", 0)
                display_text = f"{name} (Lv.{level}) [{respawn_timer}s]\nKDA: {kills} / {deaths} / {assists}"
                self.info_label.config(text=display_text, fg="#475569", font=("Meiryo UI", 11, "bold"))
                self.title_label.config(text="STRONGEST ENEMY", fg="#64748b")
            else:
                display_text = f"{name} (Lv.{level})\nKDA: {kills} / {deaths} / {assists}"
                
                # ゴールド格差（パーセント）に応じた条件付きカラーリング
                if enemy_pct >= 140:
                    self.info_label.config(text=display_text, fg="#f87171", font=("Meiryo UI", 11, "bold"))
                    self.title_label.config(text="STRONGEST ENEMY (DANGER)", fg="#ff4655")
                elif enemy_pct >= 110:
                    self.info_label.config(text=display_text, fg="#fcd34d", font=("Meiryo UI", 11, "bold"))
                    self.title_label.config(text="STRONGEST ENEMY (WARN)", fg="#fbbf24")
                else:
                    self.info_label.config(text=display_text, fg="#e2e8f0", font=("Meiryo UI", 11, "bold"))
                    self.title_label.config(text="STRONGEST ENEMY", fg="#ff4655")

            # ジオメトリを広げてキャンバスを表示
            self.root.geometry("270x165")
            self.canvas.pack(fill="both", expand=True, padx=6, pady=(0, 6))
            
            # キャンバスの描画を更新
            self.canvas.delete("all")
            
            # 最大スケールの計算
            max_val = max(150, avg_pct, my_pct, enemy_pct)
            
            # 描画パラメータ
            x_start = 90
            bar_max_width = 155
            
            # AVG描画
            self.canvas.create_text(5, 12, text="AVG  100%", anchor="w", fill="#a0aab8", font=("Meiryo UI", 9, "bold"))
            avg_width = (avg_pct / max_val) * bar_max_width
            self.canvas.create_rectangle(x_start, 6, x_start + avg_width, 16, fill="#3b82f6", width=0)
            
            # YOU描画
            self.canvas.create_text(5, 32, text=f"YOU  {my_pct}%", anchor="w", fill="#a0aab8", font=("Meiryo UI", 9, "bold"))
            my_width = (my_pct / max_val) * bar_max_width
            self.canvas.create_rectangle(x_start, 26, x_start + my_width, 36, fill="#10b981", width=0)
            
            # OP描画
            op_color = "#a0aab8"
            if enemy_pct >= 140:
                op_color = "#ff4655"
            elif enemy_pct >= 110:
                op_color = "#fbbf24"
            self.canvas.create_text(5, 52, text=f"OP   {enemy_pct}%", anchor="w", fill="#a0aab8", font=("Meiryo UI", 9, "bold"))
            enemy_width = (enemy_pct / max_val) * bar_max_width
            self.canvas.create_rectangle(x_start, 46, x_start + enemy_width, 56, fill=op_color, width=0)
            
        else:
            self.info_label.config(text="Waiting for game...", fg="#a0aab8", font=("Meiryo UI", 10))
            self.title_label.config(text="WAITING FOR GAME", fg="#a0aab8")
            
            # ジオメトリを縮小してキャンバスを隠す
            self.root.geometry("270x80")
            self.canvas.pack_forget()

    def process_events(self):
        if self.is_closed() or not self._widget_exists(self.root):
            self._closed = True
            return False

        self.refresh_view()
        if self.is_closed() or not self._widget_exists(self.root):
            self._closed = True
            return False

        try:
            self.root.update_idletasks()
            self.root.update()
            return True
        except tk.TclError:
            self._closed = True
            self.root = None
            return False

    def show(self):
        if not self.is_closed() and self._widget_exists(self.root):
            self.root.deiconify()

    def close(self):
        if self._closed:
            return

        self._closed = True
        if self.root is not None:
            try:
                self.root.destroy()
            except tk.TclError:
                pass
            self.root = None
