"""
server_gui.py  –  Secure Leaderboard Server  (GUI)
====================================================
Tkinter dashboard that wraps the TLS/TCP server.
Panels:
  • Left  – Start/Stop controls + Connected Clients list
  • Centre – Live Leaderboard (auto-refreshes)
  • Right  – Activity Log
"""

import socket
import threading
import ssl
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import time

# ── shared leaderboard ────────────────────────────────────────────────────────
import threading as _threading

_leaderboard: dict[str, int] = {}
_lb_lock = _threading.Lock()
_connected_clients: dict[str, str] = {}   # addr_str -> client_name
_clients_lock = _threading.Lock()

MAX_CLIENTS = 50       # breaking point – server refuses connections beyond this


def update_score(player: str, score: int) -> int:
    with _lb_lock:
        _leaderboard[player] = _leaderboard.get(player, 0) + score
        return _leaderboard[player]


def get_leaderboard() -> list[tuple[str, int]]:
    with _lb_lock:
        return sorted(_leaderboard.items(), key=lambda x: x[1], reverse=True)


# ── colours & fonts ───────────────────────────────────────────────────────────
BG          = "#0f1117"
PANEL_BG    = "#1a1d27"
ACCENT      = "#4f8ef7"
ACCENT2     = "#f7c04f"
GREEN       = "#3ddc84"
RED         = "#ff5c5c"
TEXT        = "#e8eaf0"
MUTED       = "#6b7080"
FONT_BODY   = ("Segoe UI", 10)
FONT_BOLD   = ("Segoe UI", 10, "bold")
FONT_TITLE  = ("Segoe UI", 13, "bold")
FONT_MONO   = ("Consolas", 9)
FONT_BIG    = ("Segoe UI", 22, "bold")


class ServerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Leaderboard Server  –  Dashboard")
        self.geometry("1100x680")
        self.minsize(900, 560)
        self.configure(bg=BG)

        self._server_socket = None
        self._running = False
        self._log_lock = _threading.Lock()

        self._build_ui()
        self._refresh_leaderboard()

    # ── UI construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        # ── top bar ──────────────────────────────────────────────────────────
        top = tk.Frame(self, bg=BG, pady=8)
        top.pack(fill="x", padx=16)

        tk.Label(top, text="⬡  Leaderboard Server", font=("Segoe UI", 15, "bold"),
                 fg=ACCENT, bg=BG).pack(side="left")

        self._status_dot = tk.Label(top, text="●", font=("Segoe UI", 14),
                                    fg=RED, bg=BG)
        self._status_dot.pack(side="right", padx=(0, 4))
        self._status_lbl = tk.Label(top, text="Offline", font=FONT_BOLD,
                                    fg=RED, bg=BG)
        self._status_lbl.pack(side="right", padx=(0, 8))

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=16)

        # ── body: three columns ───────────────────────────────────────────────
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=10)

        self._build_left(body)
        self._build_centre(body)
        self._build_right(body)

    def _panel(self, parent, title, width=None):
        """Returns the inner content Frame of a titled panel."""
        outer = tk.Frame(parent, bg=PANEL_BG, bd=0,
                         highlightthickness=1, highlightbackground="#2e3248")
        if width:
            outer.pack(side="left", fill="both", padx=(0, 10), ipadx=6, ipady=6)
            outer.pack_propagate(False)
            outer.configure(width=width)
        else:
            outer.pack(side="left", fill="both", expand=True, padx=(0, 10),
                       ipadx=6, ipady=6)
        tk.Label(outer, text=title, font=FONT_TITLE, fg=ACCENT, bg=PANEL_BG,
                 anchor="w").pack(fill="x", padx=10, pady=(8, 4))
        ttk.Separator(outer, orient="horizontal").pack(fill="x", padx=8)
        inner = tk.Frame(outer, bg=PANEL_BG)
        inner.pack(fill="both", expand=True, padx=8, pady=8)
        return inner

    def _build_left(self, parent):
        inner = self._panel(parent, "⚙  Controls & Clients", width=270)

        # HOST / PORT inputs
        tk.Label(inner, text="Host", font=FONT_BOLD, fg=TEXT, bg=PANEL_BG).grid(
            row=0, column=0, sticky="w", pady=2)
        self._host_var = tk.StringVar(value="0.0.0.0")
        tk.Entry(inner, textvariable=self._host_var, font=FONT_BODY,
                 bg="#252838", fg=TEXT, insertbackground=TEXT,
                 relief="flat", width=18).grid(row=0, column=1, pady=2, padx=(4, 0))

        tk.Label(inner, text="Port", font=FONT_BOLD, fg=TEXT, bg=PANEL_BG).grid(
            row=1, column=0, sticky="w", pady=2)
        self._port_var = tk.StringVar(value="5000")
        tk.Entry(inner, textvariable=self._port_var, font=FONT_BODY,
                 bg="#252838", fg=TEXT, insertbackground=TEXT,
                 relief="flat", width=18).grid(row=1, column=1, pady=2, padx=(4, 0))

        # Start / Stop buttons
        btn_row = tk.Frame(inner, bg=PANEL_BG)
        btn_row.grid(row=2, column=0, columnspan=2, pady=(10, 4), sticky="ew")

        self._start_btn = tk.Button(btn_row, text="▶  Start Server",
                                    font=FONT_BOLD, bg=GREEN, fg="#0f1117",
                                    relief="flat", padx=10, pady=5,
                                    command=self._start_server, cursor="hand2")
        self._start_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self._stop_btn = tk.Button(btn_row, text="■  Stop",
                                   font=FONT_BOLD, bg=RED, fg="white",
                                   relief="flat", padx=10, pady=5,
                                   command=self._stop_server, state="disabled",
                                   cursor="hand2")
        self._stop_btn.pack(side="left", fill="x", expand=True)

        tk.Button(inner, text="🗑  Reset Leaderboard", font=FONT_BODY,
          bg="#2e3248",
          fg="black",
          disabledforeground="black",
          relief="flat",
          pady=4,
          command=self._reset_board,
          cursor="hand2").grid(
    row=3, column=0, columnspan=2, sticky="ew", pady=(2, 10))

        ttk.Separator(inner, orient="horizontal").grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=4)

        tk.Label(inner, text="Connected Clients", font=FONT_BOLD,
                 fg=ACCENT2, bg=PANEL_BG).grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(4, 2))

        self._clients_box = tk.Listbox(inner, font=FONT_MONO,
                                       bg="#252838", fg=GREEN,
                                       selectbackground=ACCENT,
                                       relief="flat", bd=0,
                                       highlightthickness=0,
                                       height=12)
        self._clients_box.grid(row=6, column=0, columnspan=2,
                                sticky="nsew", pady=2)
        inner.rowconfigure(6, weight=1)
        inner.columnconfigure(1, weight=1)

        self._client_count = tk.Label(inner, text="0 clients", font=FONT_BODY,
                                      fg=MUTED, bg=PANEL_BG)
        self._client_count.grid(row=7, column=0, columnspan=2, sticky="e")

    def _build_centre(self, parent):
        inner = self._panel(parent, "🏆  Live Leaderboard", width=300)

        # stat row
        stat_row = tk.Frame(inner, bg=PANEL_BG)
        stat_row.pack(fill="x", pady=(0, 6))
        self._total_players = tk.Label(stat_row, text="0", font=FONT_BIG,
                                       fg=ACCENT, bg=PANEL_BG)
        self._total_players.pack(side="left")
        tk.Label(stat_row, text=" players", font=FONT_BODY,
                 fg=MUTED, bg=PANEL_BG).pack(side="left", pady=(8, 0))

        # leaderboard table
        cols = ("rank", "player", "score")
        style = ttk.Style()
        style.theme_use("default")
        style.configure("LB.Treeview",
                        background="#252838", foreground=TEXT,
                        rowheight=28, fieldbackground="#252838",
                        font=FONT_BODY, borderwidth=0)
        style.configure("LB.Treeview.Heading",
                        background=PANEL_BG, foreground=ACCENT,
                        font=FONT_BOLD, relief="flat")
        style.map("LB.Treeview", background=[("selected", ACCENT)])

        self._tree = ttk.Treeview(inner, columns=cols, show="headings",
                                  style="LB.Treeview", selectmode="none")
        self._tree.heading("rank",   text="#")
        self._tree.heading("player", text="Player")
        self._tree.heading("score",  text="Score")
        self._tree.column("rank",   width=40,  anchor="center")
        self._tree.column("player", width=140, anchor="w")
        self._tree.column("score",  width=80,  anchor="center")

        sb = ttk.Scrollbar(inner, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")

        # medal tag colours
        self._tree.tag_configure("gold",   foreground="#ffd700", font=FONT_BOLD)
        self._tree.tag_configure("silver", foreground="#c0c0c0", font=FONT_BOLD)
        self._tree.tag_configure("bronze", foreground="#cd7f32", font=FONT_BOLD)
        self._tree.tag_configure("normal", foreground=TEXT)

    def _build_right(self, parent):
        inner = self._panel(parent, "📋  Activity Log")

        self._log_box = scrolledtext.ScrolledText(
            inner, font=FONT_MONO, bg="#0d0f18", fg=TEXT,
            insertbackground=TEXT, relief="flat",
            state="disabled", wrap="word")
        self._log_box.pack(fill="both", expand=True)

        # colour tags for log lines
        self._log_box.tag_config("info",    foreground=ACCENT)
        self._log_box.tag_config("update",  foreground=GREEN)
        self._log_box.tag_config("get",     foreground=ACCENT2)
        self._log_box.tag_config("error",   foreground=RED)
        self._log_box.tag_config("connect", foreground="#a78bfa")
        self._log_box.tag_config("disco",   foreground=MUTED)
        self._log_box.tag_config("time",    foreground=MUTED)

        tk.Button(inner, text="Clear Log", font=FONT_BODY,
          bg="#2e3248",
          fg="black",
          disabledforeground="black",
          relief="flat",
          pady=2,
          command=self._clear_log,
          cursor="hand2").pack(
    anchor="e", pady=(4, 0))

    # ── server logic ──────────────────────────────────────────────────────────
    def _start_server(self):
        host = self._host_var.get().strip()
        try:
            port = int(self._port_var.get().strip())
        except ValueError:
            messagebox.showerror("Invalid Port", "Port must be an integer.")
            return

        try:
            raw = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            raw.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            self._ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            self._ctx.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

            raw.bind((host, port))
            raw.listen()
            self._server_socket = raw
        except Exception as exc:
            messagebox.showerror("Server Error", str(exc))
            return

        self._running = True
        self._start_btn.config(state="disabled")
        self._stop_btn.config(state="normal")
        self._status_dot.config(fg=GREEN)
        self._status_lbl.config(fg=GREEN, text="Online")
        self._log(f"Server started on {host}:{port}  (max clients: {MAX_CLIENTS})", "info")

        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _stop_server(self):
        self._running = False
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass
            self._server_socket = None
        self._start_btn.config(state="normal")
        self._stop_btn.config(state="disabled")
        self._status_dot.config(fg=RED)
        self._status_lbl.config(fg=RED, text="Offline")
        self._log("Server stopped.", "error")

    def _reset_board(self):
        with _lb_lock:
            _leaderboard.clear()
        self._log("Leaderboard reset.", "info")
        self._refresh_leaderboard()

    def _accept_loop(self):
        while self._running:
            try:
                self._server_socket.settimeout(1.0)
                conn, addr = self._server_socket.accept()
            except socket.timeout:
                continue
            except Exception:
                break

            try:
                conn = self._ctx.wrap_socket(conn, server_side=True)
                self._log(f"[SSL CONNECTED] {addr}", "connect")
            except ssl.SSLError as e:
                self._log(f"[SSL ERROR] {addr}: {e}", "error")
                conn.close()
                continue

            # ── breaking point: reject if at MAX_CLIENTS capacity ─────────
            with _clients_lock:
                current = len(_connected_clients)
            if current >= MAX_CLIENTS:
                self._log(
                    f"[LIMIT REACHED] Rejecting {addr} — at capacity ({MAX_CLIENTS})",
                    "error")
                try:
                    conn.send(f"SERVER_FULL max={MAX_CLIENTS}\n".encode())
                except Exception:
                    pass
                conn.close()
                continue
            # ─────────────────────────────────────────────────────────────

            threading.Thread(target=self._handle_client,
                             args=(conn, addr), daemon=True).start()

    def _handle_client(self, conn, addr):
        addr_str = f"{addr[0]}:{addr[1]}"
        client_name = "Unknown"
        try:
            conn.send("NAME?\n".encode())
            name_data = conn.recv(1024).decode().strip()
            if name_data:
                client_name = name_data

            self._log(f"[IDENTIFIED] '{client_name}' from {addr_str}", "connect")
            with _clients_lock:
                _connected_clients[addr_str] = client_name
            self._refresh_clients()

            while True:
                data = conn.recv(1024)
                if not data:
                    break

                parts = data.decode().strip().split()
                if not parts:
                    continue
                cmd = parts[0]

                if cmd == "UPDATE" and len(parts) == 3:
                    player = parts[1]
                    try:
                        score = int(parts[2])
                    except ValueError:
                        conn.send("Invalid score format\n".encode())
                        continue

                    new_total = update_score(player, score)
                    self._log(
                        f"[UPDATE] '{client_name}' → '{player}' +{score} (total {new_total})",
                        "update")
                    conn.send("Score updated\n".encode())
                    self.after(0, self._refresh_leaderboard)

                elif cmd == "GET":
                    self._log(f"[GET]    '{client_name}' requested leaderboard", "get")
                    board = get_leaderboard()
                    result = "\n".join(f"{p}: {s}" for p, s in board)
                    conn.send((result + "\n").encode())

                else:
                    self._log(f"[INVALID] '{client_name}' sent: {parts}", "error")
                    conn.send("Invalid command\n".encode())

        except Exception as e:
            self._log(f"[ERROR] '{client_name}' {addr_str}: {e}", "error")
        finally:
            conn.close()
            with _clients_lock:
                _connected_clients.pop(addr_str, None)
            self._log(f"[DISCONNECTED] '{client_name}' ({addr_str})", "disco")
            self._refresh_clients()

    # ── UI refresh helpers ────────────────────────────────────────────────────
    def _refresh_leaderboard(self):
        board = get_leaderboard()
        self._total_players.config(text=str(len(board)))
        for row in self._tree.get_children():
            self._tree.delete(row)
        medals = ["🥇", "🥈", "🥉"]
        tags   = ["gold", "silver", "bronze"]
        for i, (player, score) in enumerate(board):
            rank = medals[i] if i < 3 else str(i + 1)
            tag  = tags[i] if i < 3 else "normal"
            self._tree.insert("", "end", values=(rank, player, score), tags=(tag,))
        self.after(2000, self._refresh_leaderboard)

    def _refresh_clients(self):
        def _do():
            with _clients_lock:
                items = list(_connected_clients.values())
            self._clients_box.delete(0, "end")
            for name in items:
                self._clients_box.insert("end", f"  ● {name}")
            self._client_count.config(text=f"{len(items)} client{'s' if len(items) != 1 else ''}")
        self.after(0, _do)

    def _log(self, msg: str, tag: str = "info"):
        ts = time.strftime("%H:%M:%S")
        def _do():
            with self._log_lock:
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


# ── entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = ServerGUI()
    app.mainloop()
