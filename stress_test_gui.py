"""
stress_test_gui.py  –  Stress Test Dashboard
=============================================
Tkinter GUI for the multi-client stress tester.
Features:
  • Configure host, port, client count, requests per client
  • Launch all clients in parallel (multiprocessing)
  • Live progress bar and per-second throughput counter
  • Results summary with latency histogram (ASCII + canvas bar chart)
"""

import multiprocessing
import threading
import socket
import ssl
import random
import time
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import queue

# ── constants ─────────────────────────────────────────────────────────────────
PLAYERS = ["Palash", "Prajna", "Shristi", "Ojas", "Ojas2",
           "Alex",   "Maria",  "Chen",    "Riya", "Sam"]

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
FONT_BIG  = ("Segoe UI", 18, "bold")


# ── worker (runs in a separate process) ───────────────────────────────────────
def _run_client_worker(client_id: int, host: str, port: int,
                       n_requests: int, result_q):
    latencies = []
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        raw  = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock = ctx.wrap_socket(raw, server_hostname=host)
        sock.connect((host, port))

        # name handshake
        prompt = sock.recv(1024).decode().strip()
        if prompt == "NAME?":
            sock.send(f"StressClient-{client_id}\n".encode())

        for _ in range(n_requests):
            player = random.choice(PLAYERS)
            score  = random.randint(1, 10)
            t0 = time.time()
            sock.send(f"UPDATE {player} {score}\n".encode())
            sock.recv(1024)
            latencies.append(time.time() - t0)

        sock.close()
    except Exception as e:
        result_q.put({"error": str(e), "client_id": client_id, "latencies": []})
        return

    result_q.put({"client_id": client_id, "latencies": latencies, "error": None})


# ── GUI ───────────────────────────────────────────────────────────────────────
class StressTestGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Stress Test Dashboard")
        self.geometry("920x680")
        self.minsize(760, 520)
        self.configure(bg=BG)

        self._running   = False
        self._result_q  = queue.Queue()
        self._all_latencies: list[float] = []

        self._build_ui()

    def _panel(self, parent, title, **pack_kw):
        outer = tk.Frame(parent, bg=PANEL_BG, bd=0,
                         highlightthickness=1, highlightbackground="#2e3248")
        outer.pack(**pack_kw)
        tk.Label(outer, text=title, font=FONT_TITLE, fg=ACCENT, bg=PANEL_BG,
                 anchor="w").pack(fill="x", padx=10, pady=(8, 4))
        ttk.Separator(outer, orient="horizontal").pack(fill="x", padx=8)
        inner = tk.Frame(outer, bg=PANEL_BG)
        inner.pack(fill="both", expand=True, padx=10, pady=8)
        return inner

    def _lbl(self, p, t, **kw):
        kw.setdefault("font", FONT_BOLD); kw.setdefault("fg", TEXT)
        kw.setdefault("bg", PANEL_BG);   kw.setdefault("anchor", "w")
        return tk.Label(p, text=t, **kw)

    def _entry(self, p, var, w=14):
        return tk.Entry(p, textvariable=var, font=FONT_BODY,
                        bg="#252838", fg=TEXT, insertbackground=TEXT,
                        relief="flat", width=w)

    def _btn(self, p, t, cmd, color=ACCENT, fg="#fff", **kw):
        return tk.Button(p, text=t, font=FONT_BOLD, bg=color, fg=fg,
                         relief="flat", padx=10, pady=6,
                         command=cmd, cursor="hand2", **kw)

    # ── layout ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        top = tk.Frame(self, bg=BG, pady=8)
        top.pack(fill="x", padx=16)
        tk.Label(top, text="⚡  Stress Test Dashboard",
                 font=("Segoe UI", 15, "bold"), fg=ACCENT, bg=BG).pack(side="left")
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=16)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=10)

        # left column
        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="y", padx=(0, 10))
        self._build_config(left)
        self._build_progress(left)

        # right column
        right = tk.Frame(body, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        self._build_results(right)
        self._build_log(right)

    def _build_config(self, parent):
        inner = self._panel(parent, "⚙  Configuration",
                            fill="x", pady=(0, 10), ipadx=6, ipady=6)

        labels_vars = [
            ("Host",                 "host",       "10.30.201.35"),
            ("Port",                 "port",       "5000"),
            ("Number of Clients",    "n_clients",  "20"),
            ("Requests per Client",  "n_requests", "5"),
        ]
        self._cfg: dict[str, tk.StringVar] = {}
        for row, (lbl, key, default) in enumerate(labels_vars):
            self._lbl(inner, lbl).grid(row=row, column=0, sticky="w", pady=2)
            var = tk.StringVar(value=default)
            self._cfg[key] = var
            self._entry(inner, var, w=16).grid(row=row, column=1, sticky="ew",
                                               padx=(8, 0), pady=2)
        inner.columnconfigure(1, weight=1)

        # client slider
        self._lbl(inner, "Clients (slider)").grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(10, 2))
        self._client_slider = tk.Scale(
            inner, from_=1, to=100, orient="horizontal",
            variable=self._cfg["n_clients"],
            bg=PANEL_BG, fg=TEXT, troughcolor="#252838",
            highlightthickness=0, font=FONT_BODY)
        self._client_slider.grid(row=5, column=0, columnspan=2, sticky="ew")

        btn_row = tk.Frame(inner, bg=PANEL_BG)
        btn_row.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        self._start_btn = self._btn(btn_row, "▶  Run Test",
                                    self._start_test, color=GREEN, fg="#0f1117")
        self._start_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self._stop_btn = self._btn(btn_row, "■  Stop",
                                   self._stop_test, color=RED, state="disabled")
        self._stop_btn.pack(side="left", fill="x", expand=True)

    def _build_progress(self, parent):
        inner = self._panel(parent, "📊  Progress",
                            fill="x", ipadx=6, ipady=6)

        self._prog_bar = ttk.Progressbar(inner, mode="determinate")
        self._prog_bar.pack(fill="x", pady=(0, 6))

        stats = tk.Frame(inner, bg=PANEL_BG)
        stats.pack(fill="x")
        for col, (title, attr) in enumerate([
            ("Completed", "_stat_done"),
            ("Errors",    "_stat_err"),
            ("Elapsed",   "_stat_time"),
        ]):
            f = tk.Frame(stats, bg="#252838")
            f.grid(row=0, column=col, padx=(0, 6), sticky="ew")
            self._lbl(f, title, font=("Segoe UI", 8), fg=MUTED,
                      bg="#252838").pack(anchor="w", padx=6, pady=(4, 0))
            lbl = tk.Label(f, text="–", font=FONT_BIG,
                           fg=ACCENT, bg="#252838")
            lbl.pack(anchor="w", padx=6, pady=(0, 4))
            setattr(self, attr, lbl)
        stats.columnconfigure((0, 1, 2), weight=1)

    def _build_results(self, parent):
        inner = self._panel(parent, "🏁  Results",
                            fill="x", pady=(0, 10), ipadx=6, ipady=6)

        metrics = tk.Frame(inner, bg=PANEL_BG)
        metrics.pack(fill="x", pady=(0, 8))
        metric_defs = [
            ("Total Requests", "_m_total"),
            ("Avg Latency",    "_m_avg"),
            ("Min Latency",    "_m_min"),
            ("Max Latency",    "_m_max"),
            ("Throughput",     "_m_tput"),
            ("Errors",         "_m_err"),
        ]
        for col, (title, attr) in enumerate(metric_defs):
            f = tk.Frame(metrics, bg="#252838", padx=8, pady=6)
            f.grid(row=0, column=col, padx=(0, 4), sticky="ew")
            self._lbl(f, title, font=("Segoe UI", 8), fg=MUTED,
                      bg="#252838").pack(anchor="w")
            lbl = tk.Label(f, text="–", font=FONT_BOLD, fg=TEXT, bg="#252838")
            lbl.pack(anchor="w")
            setattr(self, attr, lbl)
        metrics.columnconfigure(list(range(len(metric_defs))), weight=1)

        # latency bar chart canvas
        self._lbl(inner, "Latency distribution (ms)").pack(anchor="w", pady=(4, 2))
        self._chart = tk.Canvas(inner, bg="#252838", height=100,
                                highlightthickness=0)
        self._chart.pack(fill="x")

    def _build_log(self, parent):
        inner = self._panel(parent, "📋  Log",
                            fill="both", expand=True, ipadx=6, ipady=6)

        self._log_box = scrolledtext.ScrolledText(
            inner, font=FONT_MONO, bg="#0d0f18", fg=TEXT,
            insertbackground=TEXT, relief="flat",
            state="disabled", wrap="word", height=8)
        self._log_box.pack(fill="both", expand=True)
        self._log_box.tag_config("info",  foreground=ACCENT)
        self._log_box.tag_config("ok",    foreground=GREEN)
        self._log_box.tag_config("error", foreground=RED)
        self._log_box.tag_config("time",  foreground=MUTED)
        tk.Button(inner, text="Clear", font=FONT_BODY,
                  bg="#2e3248", fg=TEXT, relief="flat", pady=2,
                  command=self._clear_log, cursor="hand2").pack(
            anchor="e", pady=(2, 0))

    # ── test logic ────────────────────────────────────────────────────────────
    def _start_test(self):
        try:
            host   = self._cfg["host"].get().strip()
            port   = int(self._cfg["port"].get())
            n_cl   = int(self._cfg["n_clients"].get())
            n_req  = int(self._cfg["n_requests"].get())
        except ValueError:
            messagebox.showerror("Config Error", "Port, Clients, and Requests must be integers.")
            return

        self._running = True
        self._all_latencies = []
        self._start_btn.config(state="disabled")
        self._stop_btn.config(state="normal")
        self._prog_bar.config(maximum=n_cl, value=0)
        self._stat_done.config(text="0")
        self._stat_err.config(text="0")
        self._stat_time.config(text="0s")
        self._log(f"Starting {n_cl} clients × {n_req} requests → {host}:{port}", "info")

        threading.Thread(target=self._run_test,
                         args=(host, port, n_cl, n_req), daemon=True).start()

    def _stop_test(self):
        self._running = False
        self._log("Test stopped by user.", "error")
        self._start_btn.config(state="normal")
        self._stop_btn.config(state="disabled")

    def _run_test(self, host, port, n_cl, n_req):
        manager   = multiprocessing.Manager()
        mp_results = manager.list()
        processes  = []
        t0         = time.time()
        done       = 0
        errors     = 0

        for i in range(n_cl):
            if not self._running:
                break
            p = multiprocessing.Process(
                target=_run_client_worker,
                args=(i, host, port, n_req, mp_results)
            )
            p.start()
            processes.append(p)

        for p in processes:
            if not self._running:
                break
            p.join()
            # drain available results
            while True:
                # poll mp_results new items
                try:
                    res = mp_results[done + errors]
                except IndexError:
                    break
                if res.get("error"):
                    errors += 1
                    self._log(f"Client {res['client_id']} error: {res['error']}", "error")
                else:
                    done += 1
                    self._all_latencies.extend(res["latencies"])
                elapsed = time.time() - t0
                self.after(0, lambda d=done, e=errors, el=elapsed:
                           self._update_progress(d, e, el))

        elapsed = time.time() - t0
        self.after(0, lambda: self._finish(n_cl, n_req, elapsed, errors))

    def _update_progress(self, done, errors, elapsed):
        self._prog_bar.config(value=done)
        self._stat_done.config(text=str(done))
        self._stat_err.config(text=str(errors),
                               fg=RED if errors else TEXT)
        self._stat_time.config(text=f"{elapsed:.1f}s")

    def _finish(self, n_cl, n_req, elapsed, errors):
        self._running = False
        self._start_btn.config(state="normal")
        self._stop_btn.config(state="disabled")

        lats = self._all_latencies
        if not lats:
            self._log("No results collected.", "error")
            return

        total   = n_cl * n_req
        avg_lat = sum(lats) / len(lats)
        min_lat = min(lats)
        max_lat = max(lats)
        tput    = total / elapsed

        self._m_total.config(text=str(total))
        self._m_avg.config(text=f"{avg_lat*1000:.1f} ms")
        self._m_min.config(text=f"{min_lat*1000:.1f} ms")
        self._m_max.config(text=f"{max_lat*1000:.1f} ms")
        self._m_tput.config(text=f"{tput:.1f}/s")
        self._m_err.config(text=str(errors), fg=RED if errors else TEXT)

        self._log(
            f"Done. {total} reqs in {elapsed:.2f}s | "
            f"avg {avg_lat*1000:.1f}ms | {tput:.1f} req/s | {errors} errors",
            "ok")
        self._draw_chart(lats)

    # ── latency bar chart ─────────────────────────────────────────────────────
    def _draw_chart(self, lats_sec: list[float]):
        lats_ms = [l * 1000 for l in lats_sec]
        n_bins  = 12
        lo, hi  = min(lats_ms), max(lats_ms)
        step    = max((hi - lo) / n_bins, 0.001)
        bins    = [0] * n_bins
        for v in lats_ms:
            idx = min(int((v - lo) / step), n_bins - 1)
            bins[idx] += 1

        self._chart.update_idletasks()
        W = self._chart.winfo_width() or 500
        H = 100
        self._chart.delete("all")
        bar_w   = (W - 20) / n_bins
        max_cnt = max(bins) or 1
        for i, cnt in enumerate(bins):
            x0 = 10 + i * bar_w
            x1 = x0 + bar_w - 2
            y0 = H - 10 - (cnt / max_cnt) * (H - 20)
            y1 = H - 10
            self._chart.create_rectangle(x0, y0, x1, y1,
                                         fill=ACCENT, outline="")
            label_ms = f"{lo + i*step:.0f}"
            self._chart.create_text(
                (x0 + x1) / 2, H - 2,
                text=label_ms, font=("Consolas", 7), fill=MUTED, anchor="s")

    # ── log helpers ───────────────────────────────────────────────────────────
    def _log(self, msg: str, tag: str = "info"):
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
    app = StressTestGUI()
    app.mainloop()
