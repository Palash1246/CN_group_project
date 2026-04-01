"""
client_gui.py  –  Leaderboard Client  (GUI)
=============================================
Tkinter client with two modes:
  • Manual  – type UPDATE / GET commands yourself
  • Auto    – fire N random score updates automatically
Panels:
  • Left  – connection settings + mode selector
  • Centre – command input / auto controls
  • Right  – server response log + leaderboard viewer
"""

import socket
import ssl
import threading
import random
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# ── colours & fonts ───────────────────────────────────────────────────────────
BG        = "#0f1117"
PANEL_BG  = "#1a1d27"
ACCENT    = "#4f8ef7"
ACCENT2   = "#f7c04f"
GREEN     = "#3ddc84"
RED       = "#ff5c5c"
TEXT      = "#e8eaf0"
MUTED     = "#6b7080"
FONT_BODY = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE= ("Segoe UI", 13, "bold")
FONT_MONO = ("Consolas", 9)

PLAYERS = ["Palash", "Prajna", "Shristi", "Ojas", "Ojas2",
           "Alex",   "Maria",  "Chen",    "Riya", "Sam"]


class ClientGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Leaderboard Client")
        self.geometry("980x660")
        self.minsize(800, 520)
        self.configure(bg=BG)

        self._sock   = None
        self._connected = False
        self._auto_running = False
        self._lock   = threading.Lock()

        self._build_ui()

    # ── UI construction ───────────────────────────────────────────────────────
    def _panel(self, parent, title, width=None):
        outer = tk.Frame(parent, bg=PANEL_BG, bd=0,
                         highlightthickness=1, highlightbackground="#2e3248")
        kw = dict(side="left", fill="both", ipadx=6, ipady=6, padx=(0, 10))
        if width:
            outer.pack(**kw)
            outer.pack_propagate(False)
            outer.configure(width=width)
        else:
            outer.pack(**kw, expand=True)
        tk.Label(outer, text=title, font=FONT_TITLE, fg=ACCENT, bg=PANEL_BG,
                 anchor="w").pack(fill="x", padx=10, pady=(8, 4))
        ttk.Separator(outer, orient="horizontal").pack(fill="x", padx=8)
        inner = tk.Frame(outer, bg=PANEL_BG)
        inner.pack(fill="both", expand=True, padx=8, pady=8)
        return inner

    def _build_ui(self):
        # top bar
        top = tk.Frame(self, bg=BG, pady=8)
        top.pack(fill="x", padx=16)
        tk.Label(top, text="◈  Leaderboard Client", font=("Segoe UI", 15, "bold"),
                 fg=ACCENT, bg=BG).pack(side="left")
        self._conn_dot = tk.Label(top, text="●", font=("Segoe UI", 14),
                                  fg=RED, bg=BG)
        self._conn_dot.pack(side="right", padx=(0, 4))
        self._conn_lbl = tk.Label(top, text="Disconnected", font=FONT_BOLD,
                                  fg=RED, bg=BG)
        self._conn_lbl.pack(side="right", padx=(0, 8))
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=16)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=10)

        self._build_left(body)
        self._build_centre(body)
        self._build_right(body)

    def _lbl(self, parent, text, **kw):
        kw.setdefault("font", FONT_BOLD)
        kw.setdefault("fg", TEXT)
        kw.setdefault("bg", PANEL_BG)
        kw.setdefault("anchor", "w")
        return tk.Label(parent, text=text, **kw)

    def _entry(self, parent, var, **kw):
        kw.setdefault("font", FONT_BODY)
        kw.setdefault("bg", "#252838")
        kw.setdefault("fg", TEXT)
        kw.setdefault("insertbackground", TEXT)
        kw.setdefault("relief", "flat")
        return tk.Entry(parent, textvariable=var, **kw)

    def _btn(self, parent, text, cmd, color=ACCENT, fg="black", **kw):
     return tk.Button(parent,
                     text=text,
                     font=FONT_BOLD,
                     bg=color,
                     fg="black",
                     relief="flat",
                     padx=8,
                     pady=5,
                     command=cmd,
                     cursor="hand2",
                     **kw)

    # ── left panel: connection + mode ─────────────────────────────────────────
    def _build_left(self, parent):
        inner = self._panel(parent, "🔌  Connection", width=250)

        self._host_var  = tk.StringVar(value="10.30.201.35")
        self._port_var  = tk.StringVar(value="5000")
        self._name_var  = tk.StringVar(value="")

        fields = [("Host", self._host_var), ("Port", self._port_var),
                  ("Your Name", self._name_var)]
        for i, (lbl, var) in enumerate(fields):
            self._lbl(inner, lbl).grid(row=i*2, column=0, sticky="w",
                                       pady=(4, 0), columnspan=2)
            e = self._entry(inner, var, width=22)
            e.grid(row=i*2+1, column=0, sticky="ew", pady=(0, 4), columnspan=2)

        inner.columnconfigure(0, weight=1)

        self._connect_btn = self._btn(inner, "Connect", self._connect,
                                      color=GREEN, fg="#0f1117")
        self._connect_btn.grid(row=6, column=0, sticky="ew", pady=(8, 2))

        self._disconnect_btn = self._btn(inner, "Disconnect", self._disconnect,
                                         color=RED, state="disabled")
        self._disconnect_btn.grid(row=7, column=0, sticky="ew", pady=(0, 8))

        ttk.Separator(inner, orient="horizontal").grid(
            row=8, column=0, sticky="ew", pady=6)

        # mode selector
        self._lbl(inner, "Mode").grid(row=9, column=0, sticky="w")
        self._mode_var = tk.StringVar(value="manual")
        for text, val, r in [("Manual", "manual", 10), ("Auto", "auto", 11)]:
            rb = tk.Radiobutton(inner, text=text, variable=self._mode_var,
                                value=val, font=FONT_BODY,
                                fg=TEXT, bg=PANEL_BG,
                                selectcolor="#252838", activebackground=PANEL_BG,
                                activeforeground=TEXT,
                                command=self._on_mode_change)
            rb.grid(row=r, column=0, sticky="w", padx=(8, 0))

    # ── centre panel: command / auto controls ─────────────────────────────────
    def _build_centre(self, parent):
        inner = self._panel(parent, "🎮  Commands", width=310)

        # ── Manual section ────────────────────────────────────────────────────
        self._manual_frame = tk.Frame(inner, bg=PANEL_BG)
        self._manual_frame.pack(fill="x")

        self._lbl(self._manual_frame, "UPDATE  – add score").pack(
            anchor="w", pady=(0, 2))

        row1 = tk.Frame(self._manual_frame, bg=PANEL_BG)
        row1.pack(fill="x", pady=2)
        self._upd_player_var = tk.StringVar()
        self._lbl(row1, "Player", font=FONT_BODY).pack(side="left")
        self._entry(row1, self._upd_player_var, width=12).pack(
            side="left", padx=(4, 8))

        self._upd_score_var = tk.StringVar()
        self._lbl(row1, "Score", font=FONT_BODY).pack(side="left")
        self._entry(row1, self._upd_score_var, width=6).pack(
            side="left", padx=4)

        self._btn(self._manual_frame, "▶  Send UPDATE",
                  self._send_update, color=ACCENT).pack(
            fill="x", pady=(4, 10))

        ttk.Separator(self._manual_frame, orient="horizontal").pack(
            fill="x", pady=4)

        self._lbl(self._manual_frame, "GET  – fetch leaderboard").pack(
            anchor="w", pady=(4, 2))
        self._btn(self._manual_frame, "📊  Send GET",
                  self._send_get, color=ACCENT2, fg="#0f1117").pack(
            fill="x", pady=(2, 8))

        ttk.Separator(self._manual_frame, orient="horizontal").pack(
            fill="x", pady=4)

        self._lbl(self._manual_frame, "Raw command").pack(anchor="w", pady=(4, 2))
        self._raw_var = tk.StringVar()
        raw_entry = self._entry(self._manual_frame, self._raw_var)
        raw_entry.pack(fill="x", pady=(0, 4))
        raw_entry.bind("<Return>", lambda _: self._send_raw())
        self._btn(self._manual_frame, "⏎  Send Raw",
                  self._send_raw, color="#3d4460").pack(fill="x")

        # ── Auto section ──────────────────────────────────────────────────────
        self._auto_frame = tk.Frame(inner, bg=PANEL_BG)

        self._lbl(self._auto_frame, "Number of updates").pack(anchor="w", pady=(0, 2))
        self._num_updates_var = tk.IntVar(value=10)
        tk.Scale(self._auto_frame, from_=1, to=100,
                 orient="horizontal", variable=self._num_updates_var,
                 bg=PANEL_BG, fg=TEXT, troughcolor="#252838",
                 highlightthickness=0, font=FONT_BODY).pack(fill="x")

        self._lbl(self._auto_frame, "Delay between updates (s)").pack(
            anchor="w", pady=(8, 2))
        self._delay_var = tk.DoubleVar(value=0.5)
        tk.Scale(self._auto_frame, from_=0.1, to=3.0, resolution=0.1,
                 orient="horizontal", variable=self._delay_var,
                 bg=PANEL_BG, fg=TEXT, troughcolor="#252838",
                 highlightthickness=0, font=FONT_BODY).pack(fill="x")

        self._lbl(self._auto_frame, "Score range").pack(
            anchor="w", pady=(8, 2))
        rng = tk.Frame(self._auto_frame, bg=PANEL_BG)
        rng.pack(fill="x")
        self._score_min_var = tk.IntVar(value=1)
        self._score_max_var = tk.IntVar(value=10)
        self._lbl(rng, "Min", font=FONT_BODY).pack(side="left")
        self._entry(rng, self._score_min_var, width=5).pack(
            side="left", padx=(4, 12))
        self._lbl(rng, "Max", font=FONT_BODY).pack(side="left")
        self._entry(rng, self._score_max_var, width=5).pack(
            side="left", padx=4)

        self._auto_progress = ttk.Progressbar(self._auto_frame, mode="determinate")
        self._auto_progress.pack(fill="x", pady=(10, 4))
        self._auto_status_lbl = tk.Label(self._auto_frame, text="",
                                         font=FONT_BODY, fg=MUTED, bg=PANEL_BG)
        self._auto_status_lbl.pack(anchor="w")

        auto_btns = tk.Frame(self._auto_frame, bg=PANEL_BG)
        auto_btns.pack(fill="x", pady=(8, 0))
        self._auto_start_btn = self._btn(auto_btns, "▶  Start Auto",
                                         self._start_auto, color=GREEN, fg="#0f1117")
        self._auto_start_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self._auto_stop_btn  = self._btn(auto_btns, "■  Stop",
                                         self._stop_auto, color=RED,
                                         state="disabled")
        self._auto_stop_btn.pack(side="left", fill="x", expand=True)

        # show manual by default
        self._manual_frame.pack(fill="x")

    # ── right panel: log + leaderboard ────────────────────────────────────────
    def _build_right(self, parent):
        inner = self._panel(parent, "📋  Log & Leaderboard")

        nb = ttk.Notebook(inner)
        nb.pack(fill="both", expand=True)

        # -- Log tab --
        log_tab = tk.Frame(nb, bg="#0d0f18")
        nb.add(log_tab, text="  Activity Log  ")

        self._log_box = scrolledtext.ScrolledText(
            log_tab, font=FONT_MONO, bg="#0d0f18", fg=TEXT,
            insertbackground=TEXT, relief="flat",
            state="disabled", wrap="word")
        self._log_box.pack(fill="both", expand=True)
        self._log_box.tag_config("sent",    foreground=ACCENT)
        self._log_box.tag_config("recv",    foreground=GREEN)
        self._log_box.tag_config("system",  foreground=ACCENT2)
        self._log_box.tag_config("error",   foreground=RED)
        self._log_box.tag_config("time",    foreground=MUTED)

        tk.Button(log_tab, text="Clear", font=FONT_BODY,
          bg="#2e3248",
          fg="black",
          disabledforeground="black",
          relief="flat",
          pady=2,
          command=self._clear_log,
          cursor="hand2").pack(
            anchor="e", padx=4, pady=2)

        # -- Leaderboard tab --
        lb_tab = tk.Frame(nb, bg=PANEL_BG)
        nb.add(lb_tab, text="  Leaderboard  ")

        style = ttk.Style()
        style.configure("LB2.Treeview",
                        background="#252838", foreground=TEXT,
                        rowheight=28, fieldbackground="#252838",
                        font=FONT_BODY)
        style.configure("LB2.Treeview.Heading",
                        background=PANEL_BG, foreground=ACCENT,
                        font=FONT_BOLD, relief="flat")
        style.map("LB2.Treeview", background=[("selected", ACCENT)])

        cols = ("rank", "player", "score")
        self._lb_tree = ttk.Treeview(lb_tab, columns=cols,
                                     show="headings", style="LB2.Treeview",
                                     selectmode="none")
        self._lb_tree.heading("rank",   text="#")
        self._lb_tree.heading("player", text="Player")
        self._lb_tree.heading("score",  text="Score")
        self._lb_tree.column("rank",   width=50,  anchor="center")
        self._lb_tree.column("player", width=150, anchor="w")
        self._lb_tree.column("score",  width=80,  anchor="center")
        self._lb_tree.tag_configure("gold",   foreground="#ffd700", font=FONT_BOLD)
        self._lb_tree.tag_configure("silver", foreground="#c0c0c0", font=FONT_BOLD)
        self._lb_tree.tag_configure("bronze", foreground="#cd7f32", font=FONT_BOLD)
        self._lb_tree.tag_configure("normal", foreground=TEXT)

        sb2 = ttk.Scrollbar(lb_tab, orient="vertical",
                            command=self._lb_tree.yview)
        self._lb_tree.configure(yscrollcommand=sb2.set)
        self._lb_tree.pack(side="left", fill="both", expand=True)
        sb2.pack(side="left", fill="y")

        self._btn(lb_tab, "🔄  Refresh", self._send_get,
                  color="#2e3248").pack(side="bottom", fill="x",
                                        padx=4, pady=4)

    # ── connection ────────────────────────────────────────────────────────────
    def _connect(self):
        host = self._host_var.get().strip()
        name = self._name_var.get().strip()
        if not name:
            messagebox.showerror("Name required", "Please enter your client name.")
            return
        try:
            port = int(self._port_var.get().strip())
        except ValueError:
            messagebox.showerror("Invalid Port", "Port must be an integer.")
            return

        def _do():
            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode    = ssl.CERT_NONE
                raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._sock = ctx.wrap_socket(raw, server_hostname=host)
                self._sock.connect((host, port))

                self._log("[SSL CONNECTED] Secure connection established", "system")

                prompt = self._sock.recv(1024).decode().strip()

                # ── breaking point: server at 50-client capacity ──────────
                if prompt.startswith("SERVER_FULL"):
                    limit = prompt.split("=")[-1] if "=" in prompt else "50"
                    self._log(
                        f"[REJECTED] Server full (max {limit} clients). Try again later.",
                        "error")
                    self._sock.close()
                    self._sock = None
                    self.after(0, lambda: messagebox.showerror(
                        "Server Full",
                        f"Server has reached its limit of {limit} clients.\n"
                        "Please try again later."))
                    return
                # ─────────────────────────────────────────────────────────

                if prompt == "NAME?":
                    self._sock.send((name + "\n").encode())
                    self._log(f"[REGISTERED] Connected as '{name}'", "system")

                self._connected = True
                self.after(0, self._on_connect_success)
            except Exception as e:
                self._log(f"[ERROR] {e}", "error")
                self.after(0, lambda: messagebox.showerror("Connect Error", str(e)))

        threading.Thread(target=_do, daemon=True).start()

    def _on_connect_success(self):
        self._conn_dot.config(fg=GREEN)
        self._conn_lbl.config(fg=GREEN,
                               text=f"Connected as '{self._name_var.get().strip()}'")
        self._connect_btn.config(state="disabled")
        self._disconnect_btn.config(state="normal")

    def _disconnect(self):
        self._connected = False
        self._auto_running = False
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None
        self._conn_dot.config(fg=RED)
        self._conn_lbl.config(fg=RED, text="Disconnected")
        self._connect_btn.config(state="normal")
        self._disconnect_btn.config(state="disabled")
        self._log("[DISCONNECTED] Connection closed.", "system")

    # ── mode switch ───────────────────────────────────────────────────────────
    def _on_mode_change(self):
        if self._mode_var.get() == "manual":
            self._auto_frame.pack_forget()
            self._manual_frame.pack(fill="x")
        else:
            self._manual_frame.pack_forget()
            self._auto_frame.pack(fill="x")

    # ── commands ──────────────────────────────────────────────────────────────
    def _send(self, msg: str) -> str | None:
        if not self._connected or not self._sock:
            self._log("[ERROR] Not connected.", "error")
            return None
        try:
            self._sock.send((msg.strip() + "\n").encode())
            self._log(f"→ {msg.strip()}", "sent")
            resp = self._sock.recv(4096).decode()
            self._log(f"← {resp.strip()}", "recv")
            return resp
        except Exception as e:
            self._log(f"[ERROR] {e}", "error")
            self._connected = False
            return None

    def _send_update(self):
        player = self._upd_player_var.get().strip()
        score  = self._upd_score_var.get().strip()
        if not player or not score:
            messagebox.showerror("Missing fields", "Enter both player name and score.")
            return
        threading.Thread(target=lambda: self._send(f"UPDATE {player} {score}"),
                         daemon=True).start()

    def _send_get(self):
        def _do():
            resp = self._send("GET")
            if resp:
                self.after(0, lambda: self._update_lb_tree(resp))
        threading.Thread(target=_do, daemon=True).start()

    def _send_raw(self):
        msg = self._raw_var.get().strip()
        if not msg:
            return
        self._raw_var.set("")
        threading.Thread(target=lambda: self._send(msg), daemon=True).start()

    def _update_lb_tree(self, raw: str):
        for row in self._lb_tree.get_children():
            self._lb_tree.delete(row)
        medals = ["🥇", "🥈", "🥉"]
        tags   = ["gold", "silver", "bronze"]
        for i, line in enumerate(raw.strip().splitlines()):
            parts = line.split(":", 1)
            if len(parts) == 2:
                player = parts[0].strip()
                score  = parts[1].strip()
                rank   = medals[i] if i < 3 else str(i + 1)
                tag    = tags[i] if i < 3 else "normal"
                self._lb_tree.insert("", "end", values=(rank, player, score),
                                     tags=(tag,))

    # ── auto mode ─────────────────────────────────────────────────────────────
    def _start_auto(self):
        if not self._connected:
            messagebox.showerror("Not connected", "Connect to the server first.")
            return
        self._auto_running = True
        self._auto_start_btn.config(state="disabled")
        self._auto_stop_btn.config(state="normal")
        threading.Thread(target=self._auto_loop, daemon=True).start()

    def _stop_auto(self):
        self._auto_running = False
        self._auto_start_btn.config(state="normal")
        self._auto_stop_btn.config(state="disabled")
        self._auto_status_lbl.config(text="Stopped.")

    def _auto_loop(self):
        total = self._num_updates_var.get()
        delay = self._delay_var.get()
        lo    = self._score_min_var.get()
        hi    = self._score_max_var.get()
        self._auto_progress.config(maximum=total, value=0)

        for i in range(1, total + 1):
            if not self._auto_running:
                break
            player = random.choice(PLAYERS)
            score  = random.randint(lo, hi)
            self._send(f"UPDATE {player} {score}")
            self.after(0, lambda v=i: self._auto_progress.config(value=v))
            self.after(0, lambda v=i, t=total:
                       self._auto_status_lbl.config(
                           text=f"Sent {v}/{t} updates…"))
            time.sleep(delay)

        if self._auto_running:
            self.after(0, self._auto_status_lbl.config(text="Done!"))
            self.after(0, self._send_get)
        self.after(0, self._stop_auto)

    # ── log helpers ───────────────────────────────────────────────────────────
    def _log(self, msg: str, tag: str = "system"):
        ts = time.strftime("%H:%M:%S")
        def _do():
            self._log_box.config(state="normal")
            self._log_box.insert("end", f"[{ts}]  ", "time")
            self._log_box.insert("end", msg + "\n", tag)
            self._log_box.see("end")
            self._log_box.config(state="disabled")
        self.after(0, _do)

    def _clear_log(self):
        self._log_box.config(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.config(state="disabled")


if __name__ == "__main__":
    app = ClientGUI()
    app.mainloop()
