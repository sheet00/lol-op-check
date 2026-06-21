import threading
import tkinter as tk

class OverlayState:
    def __init__(self):
        self.lock = threading.Lock()
        self.data = {
            "status": "データを取得中...",
            "strongest_champion": None,
        }

    def update(self, *, status=None, strongest_champion=None):
        with self.lock:
            if status is not None:
                self.data["status"] = status
            if strongest_champion is not None:
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

        # 画面左上に配置 (幅 250px, 高さ 80px, x=10, y=10)
        self.root.geometry("250x80+10+10")
        
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

        # 閉じるボタン
        self.close_button = tk.Button(
            self.frame,
            text="×",
            command=self.close,
            bg="#141a24",
            fg="#a0aab8",
            bd=0,
            font=("Meiryo UI", 9, "bold"),
            activebackground="#202938",
            activeforeground="#f5f7fb",
        )
        self.close_button.place(relx=1.0, x=-6, y=6, anchor="ne", width=20, height=20)

        # タイトル表示
        self.title_label = tk.Label(
            self.frame,
            text="MOST POWERFUL CHAMPION",
            anchor="nw",
            bg="#080c12",
            fg="#ff4655", # 警告色っぽい鮮やかなネオンレッド
            font=("Meiryo UI", 9, "bold"),
            padx=8,
            pady=4,
        )
        self.title_label.pack(fill="x")

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

        # ドラッグ可能にするためのバインド
        for widget in (self.root, self.frame, self.title_label, self.info_label):
            widget.bind("<ButtonPress-1>", self._start_drag)
            widget.bind("<B1-Motion>", self._drag)
            widget.bind("<Button-3>", self._handle_close_event)

        self.root.bind("<Escape>", self._handle_close_event)
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

    def _handle_close_event(self, _event):
        self.close()
        return "break"

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
            
            if is_dead:
                respawn_timer = champ.get("respawn_timer", 0)
                display_text = f"{name} (Lv.{level}) [DEAD ({respawn_timer}s)]\nKDA: {kills} / {deaths} / {assists}"
                self.info_label.config(text=display_text, fg="#475569", font=("Meiryo UI", 11, "bold"))
                self.title_label.config(text="STRONGEST ENEMY (DEAD)", fg="#64748b")
            else:
                display_text = f"{name} (Lv.{level})\nKDA: {kills} / {deaths} / {assists}"
                self.info_label.config(text=display_text, fg="#e2e8f0", font=("Meiryo UI", 11, "bold"))
                self.title_label.config(text="STRONGEST ENEMY", fg="#ff4655")
        else:
            self.info_label.config(text="Waiting for game...", fg="#a0aab8", font=("Meiryo UI", 10))
            self.title_label.config(text="WAITING FOR GAME", fg="#a0aab8")

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
