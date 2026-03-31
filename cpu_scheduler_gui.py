"""
CPU Scheduler Simulator — GUI App
Run: python cpu_scheduler_gui.py
Requires: pip install matplotlib
tkinter comes built-in with Python on Windows
"""

import tkinter as tk
from tkinter import ttk, messagebox
import copy
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# ── Colour palette ─────────────────────────────────────────────────────
BG        = "#0F1117"
SURFACE   = "#1A1D27"
SURFACE2  = "#22263A"
ACCENT    = "#4F8EF7"
ACCENT2   = "#7C5CFC"
SUCCESS   = "#2ECC71"
WARNING   = "#F39C12"
DANGER    = "#E74C3C"
TEXT      = "#E8EAF0"
TEXT2     = "#8B90A0"
BORDER    = "#2E3347"

PROC_COLORS = [
    "#4F8EF7","#7C5CFC","#2ECC71","#F39C12",
    "#E74C3C","#1ABC9C","#E91E8C","#FF6B35",
    "#00BCD4","#9C27B0",
]

# ── Scheduling algorithms (self-contained, no imports needed) ──────────

def fcfs(procs):
    timeline, t = [], 0
    for p in sorted(procs, key=lambda x: (x["arrival"], x["pid"])):
        if t < p["arrival"]: t = p["arrival"]
        timeline.append((p["pid"], t, t + p["burst"]))
        t += p["burst"]
    return timeline

def sjf(procs):
    timeline, t, rem = [], 0, copy.deepcopy(procs)
    while rem:
        avail = [p for p in rem if p["arrival"] <= t]
        if not avail:
            t = min(p["arrival"] for p in rem); continue
        chosen = min(avail, key=lambda p: (p["burst"], p["arrival"], p["pid"]))
        rem.remove(chosen)
        timeline.append((chosen["pid"], t, t + chosen["burst"]))
        t += chosen["burst"]
    return timeline

def srtf(procs):
    timeline = []
    remaining = {p["pid"]: p["burst"] for p in procs}
    arrivals  = {p["pid"]: p["arrival"] for p in procs}
    total = max(p["arrival"] for p in procs) + sum(p["burst"] for p in procs) + 1
    cur, seg = None, 0
    for t in range(total):
        ready = [pid for pid, r in remaining.items() if r > 0 and arrivals[pid] <= t]
        if not ready:
            if cur: timeline.append((cur, seg, t)); cur = None
            continue
        chosen = min(ready, key=lambda pid: (remaining[pid], pid))
        if chosen != cur:
            if cur: timeline.append((cur, seg, t))
            cur, seg = chosen, t
        remaining[chosen] -= 1
        if remaining[chosen] == 0:
            timeline.append((chosen, seg, t + 1))
            del remaining[chosen]; cur = None
        if not remaining: break
    return timeline

def round_robin(procs, quantum):
    from collections import deque
    timeline = []
    pool = sorted(copy.deepcopy(procs), key=lambda p: (p["arrival"], p["pid"]))
    remaining = {p["pid"]: p["burst"] for p in pool}
    arrivals  = {p["pid"]: p["arrival"] for p in pool}
    queue, idx, t = deque(), 0, 0
    while idx < len(pool) and pool[idx]["arrival"] <= t:
        queue.append(pool[idx]["pid"]); idx += 1
    while queue:
        pid = queue.popleft()
        run = min(quantum, remaining[pid])
        timeline.append((pid, t, t + run))
        t += run; remaining[pid] -= run
        while idx < len(pool) and pool[idx]["arrival"] <= t:
            queue.append(pool[idx]["pid"]); idx += 1
        if remaining[pid] > 0: queue.append(pid)
        if not queue and idx < len(pool):
            t = pool[idx]["arrival"]
            while idx < len(pool) and pool[idx]["arrival"] <= t:
                queue.append(pool[idx]["pid"]); idx += 1
    return timeline

def priority_sched(procs):
    timeline = []
    remaining = {p["pid"]: p["burst"]    for p in procs}
    arrivals  = {p["pid"]: p["arrival"]  for p in procs}
    priorities= {p["pid"]: p["priority"] for p in procs}
    total = max(p["arrival"] for p in procs) + sum(p["burst"] for p in procs) + 1
    cur, seg = None, 0
    for t in range(total):
        ready = [pid for pid, r in remaining.items() if r > 0 and arrivals[pid] <= t]
        if not ready:
            if cur: timeline.append((cur, seg, t)); cur = None
            continue
        chosen = min(ready, key=lambda pid: (priorities[pid], arrivals[pid], pid))
        if chosen != cur:
            if cur: timeline.append((cur, seg, t))
            cur, seg = chosen, t
        remaining[chosen] -= 1
        if remaining[chosen] == 0:
            timeline.append((chosen, seg, t + 1))
            del remaining[chosen]; cur = None
        if not remaining: break
    return timeline

def compute_metrics(procs, timeline):
    first_start, last_finish = {}, {}
    for pid, s, e in timeline:
        if pid not in first_start: first_start[pid] = s
        last_finish[pid] = e
    results = []
    for p in procs:
        pid = p["pid"]
        if pid not in first_start: continue
        tat  = last_finish[pid] - p["arrival"]
        wt   = tat - p["burst"]
        rt   = first_start[pid] - p["arrival"]
        results.append({**p, "start": first_start[pid], "finish": last_finish[pid],
                        "tat": tat, "wt": wt, "rt": rt})
    return results

def merge_timeline(tl):
    merged = []
    for pid, s, e in tl:
        if merged and merged[-1][0] == pid and merged[-1][2] == s:
            merged[-1] = (pid, merged[-1][1], e)
        else:
            merged.append([pid, s, e])
    return [(p, s, e) for p, s, e in merged]

# ── Main App ───────────────────────────────────────────────────────────

class CPUSchedulerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CPU Scheduler Simulator")
        self.root.geometry("1200x800")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        self.processes = []
        self.pid_counter = 1
        self.color_map = {}

        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".",            background=BG,      foreground=TEXT,   font=("Consolas", 10))
        style.configure("TFrame",       background=BG)
        style.configure("Surface.TFrame", background=SURFACE)
        style.configure("TLabel",       background=BG,      foreground=TEXT)
        style.configure("Surface.TLabel", background=SURFACE, foreground=TEXT)
        style.configure("Dim.TLabel",   background=SURFACE, foreground=TEXT2,  font=("Consolas", 9))
        style.configure("Title.TLabel", background=BG,      foreground=TEXT,   font=("Consolas", 14, "bold"))
        style.configure("Accent.TLabel",background=BG,      foreground=ACCENT, font=("Consolas", 11, "bold"))
        style.configure("TEntry",       fieldbackground=SURFACE2, foreground=TEXT,
                        insertcolor=TEXT, bordercolor=BORDER, relief="flat")
        style.configure("TCombobox",    fieldbackground=SURFACE2, foreground=TEXT,
                        background=SURFACE2, arrowcolor=TEXT2)
        style.map("TCombobox",          fieldbackground=[("readonly", SURFACE2)])
        style.configure("TButton",      background=SURFACE2, foreground=TEXT,
                        bordercolor=BORDER, relief="flat", padding=(10,6))
        style.map("TButton",            background=[("active", SURFACE)])
        style.configure("Run.TButton",  background=ACCENT,  foreground="#FFFFFF",
                        font=("Consolas", 10, "bold"), padding=(16,8))
        style.map("Run.TButton",        background=[("active", "#3A7EE8")])
        style.configure("Treeview",     background=SURFACE, foreground=TEXT,
                        fieldbackground=SURFACE, rowheight=28, borderwidth=0)
        style.configure("Treeview.Heading", background=SURFACE2, foreground=TEXT2,
                        font=("Consolas", 9, "bold"), relief="flat")
        style.map("Treeview",           background=[("selected", ACCENT2)])

    def _build_ui(self):
        # ── Header ──
        hdr = tk.Frame(self.root, bg=SURFACE, height=56)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="⚙  CPU Scheduler Simulator", bg=SURFACE,
                 fg=TEXT, font=("Consolas", 15, "bold")).pack(side="left", padx=20, pady=14)
        tk.Label(hdr, text="Python · Matplotlib · tkinter", bg=SURFACE,
                 fg=TEXT2, font=("Consolas", 9)).pack(side="right", padx=20)

        # ── Main layout ──
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=16, pady=12)

        # Left panel
        left = tk.Frame(main, bg=BG, width=340)
        left.pack(side="left", fill="y", padx=(0,12))
        left.pack_propagate(False)

        # Right panel
        self.right = tk.Frame(main, bg=BG)
        self.right.pack(side="left", fill="both", expand=True)

        self._build_left(left)
        self._build_right()

    def _build_left(self, parent):
        # Algorithm selection
        algo_frame = tk.Frame(parent, bg=SURFACE, padx=14, pady=12)
        algo_frame.pack(fill="x", pady=(0,10))
        tk.Label(algo_frame, text="ALGORITHM", bg=SURFACE, fg=TEXT2,
                 font=("Consolas", 9, "bold")).pack(anchor="w")

        self.algo_var = tk.StringVar(value="FCFS")
        algos = ["FCFS", "SJF", "SRTF", "Round Robin", "Priority"]
        for a in algos:
            tk.Radiobutton(algo_frame, text=a, variable=self.algo_var, value=a,
                           bg=SURFACE, fg=TEXT, selectcolor=SURFACE2,
                           activebackground=SURFACE, activeforeground=ACCENT,
                           font=("Consolas", 10), command=self._on_algo_change
                           ).pack(anchor="w", pady=1)

        # Quantum (RR only)
        self.quantum_frame = tk.Frame(parent, bg=SURFACE, padx=14, pady=10)
        self.quantum_frame.pack(fill="x", pady=(0,10))
        tk.Label(self.quantum_frame, text="TIME QUANTUM", bg=SURFACE, fg=TEXT2,
                 font=("Consolas", 9, "bold")).pack(anchor="w")
        self.quantum_var = tk.StringVar(value="2")
        tk.Entry(self.quantum_frame, textvariable=self.quantum_var, width=6,
                 bg=SURFACE2, fg=TEXT, insertbackground=TEXT,
                 relief="flat", font=("Consolas", 12)).pack(anchor="w", pady=4)
        self.quantum_frame.pack_forget()

        # Process input
        proc_frame = tk.Frame(parent, bg=SURFACE, padx=14, pady=12)
        proc_frame.pack(fill="x", pady=(0,10))
        tk.Label(proc_frame, text="ADD PROCESS", bg=SURFACE, fg=TEXT2,
                 font=("Consolas", 9, "bold")).pack(anchor="w", pady=(0,8))

        fields = [("Arrival Time", "arrival_var", "0"),
                  ("Burst Time",   "burst_var",   "4"),
                  ("Priority",     "priority_var","1")]
        for label, var, default in fields:
            row = tk.Frame(proc_frame, bg=SURFACE)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label, bg=SURFACE, fg=TEXT2,
                     font=("Consolas", 9), width=12, anchor="w").pack(side="left")
            setattr(self, var, tk.StringVar(value=default))
            tk.Entry(row, textvariable=getattr(self, var), width=8,
                     bg=SURFACE2, fg=TEXT, insertbackground=TEXT,
                     relief="flat", font=("Consolas", 11)).pack(side="left", padx=(4,0))

        self.priority_widgets = []  # to show/hide priority row

        btn_row = tk.Frame(proc_frame, bg=SURFACE)
        btn_row.pack(fill="x", pady=(10,0))
        tk.Button(btn_row, text="+ Add", bg=ACCENT, fg="white",
                  font=("Consolas", 10, "bold"), relief="flat",
                  padx=12, pady=6, cursor="hand2",
                  command=self._add_process).pack(side="left", padx=(0,6))
        tk.Button(btn_row, text="Clear All", bg=SURFACE2, fg=TEXT2,
                  font=("Consolas", 10), relief="flat",
                  padx=12, pady=6, cursor="hand2",
                  command=self._clear_processes).pack(side="left")

        # Process list
        list_frame = tk.Frame(parent, bg=SURFACE, padx=14, pady=12)
        list_frame.pack(fill="both", expand=True, pady=(0,10))
        tk.Label(list_frame, text="PROCESS LIST", bg=SURFACE, fg=TEXT2,
                 font=("Consolas", 9, "bold")).pack(anchor="w", pady=(0,6))

        cols = ("PID", "Arrival", "Burst", "Priority")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", height=8)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=70, anchor="center")
        self.tree.pack(fill="both", expand=True)
        tk.Button(list_frame, text="✕ Remove Selected", bg=SURFACE2, fg=DANGER,
                  font=("Consolas", 9), relief="flat", pady=4, cursor="hand2",
                  command=self._remove_selected).pack(fill="x", pady=(6,0))

        # Run button
        tk.Button(parent, text="▶  RUN SIMULATION", bg=ACCENT, fg="white",
                  font=("Consolas", 12, "bold"), relief="flat",
                  pady=12, cursor="hand2",
                  command=self._run).pack(fill="x", pady=(0,4))

        # Load demo
        tk.Button(parent, text="Load Demo Processes", bg=SURFACE, fg=TEXT2,
                  font=("Consolas", 9), relief="flat", pady=6, cursor="hand2",
                  command=self._load_demo).pack(fill="x")

    def _build_right(self):
        # Notebook tabs
        self.notebook = ttk.Notebook(self.right)
        self.notebook.pack(fill="both", expand=True)

        style = ttk.Style()
        style.configure("TNotebook",     background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=SURFACE2, foreground=TEXT2,
                        padding=(14,6), font=("Consolas", 10))
        style.map("TNotebook.Tab",       background=[("selected", SURFACE)],
                                         foreground=[("selected", TEXT)])

        # Tab 1 — Gantt
        self.gantt_tab = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.gantt_tab, text="  Gantt Chart  ")

        # Tab 2 — Metrics
        self.metrics_tab = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.metrics_tab, text="  Metrics  ")

        # Tab 3 — Details table
        self.table_tab = tk.Frame(self.notebook, bg=BG)
        self.notebook.add(self.table_tab, text="  Process Details  ")

        # Placeholder
        tk.Label(self.gantt_tab, text="Run a simulation to see the Gantt chart",
                 bg=BG, fg=TEXT2, font=("Consolas", 12)).pack(expand=True)

    def _on_algo_change(self):
        if self.algo_var.get() == "Round Robin":
            self.quantum_frame.pack(fill="x", pady=(0,10), before=self.quantum_frame.master.winfo_children()[2] if False else self.quantum_frame)
            self.quantum_frame.pack(fill="x", pady=(0, 10))
        else:
            self.quantum_frame.pack_forget()

    def _add_process(self):
        try:
            arrival  = int(self.arrival_var.get())
            burst    = int(self.burst_var.get())
            priority = int(self.priority_var.get())
            if burst < 1: raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid integers.\nBurst time must be ≥ 1.")
            return

        pid = f"P{self.pid_counter}"
        self.pid_counter += 1
        proc = {"pid": pid, "arrival": arrival, "burst": burst, "priority": priority}
        self.processes.append(proc)
        self.color_map[pid] = PROC_COLORS[len(self.processes) % len(PROC_COLORS)]
        self.tree.insert("", "end", values=(pid, arrival, burst, priority))

        # Auto-increment arrival for convenience
        self.arrival_var.set(str(arrival + burst))

    def _remove_selected(self):
        sel = self.tree.selection()
        if not sel: return
        for item in sel:
            pid = self.tree.item(item)["values"][0]
            self.processes = [p for p in self.processes if p["pid"] != pid]
            self.tree.delete(item)

    def _clear_processes(self):
        self.processes.clear()
        self.color_map.clear()
        self.pid_counter = 1
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _load_demo(self):
        self._clear_processes()
        demos = [
            {"arrival": 0, "burst": 6, "priority": 3},
            {"arrival": 2, "burst": 4, "priority": 1},
            {"arrival": 4, "burst": 2, "priority": 4},
            {"arrival": 6, "burst": 5, "priority": 2},
            {"arrival": 8, "burst": 3, "priority": 5},
        ]
        for d in demos:
            self.arrival_var.set(str(d["arrival"]))
            self.burst_var.set(str(d["burst"]))
            self.priority_var.set(str(d["priority"]))
            self._add_process()

    def _run(self):
        if not self.processes:
            messagebox.showwarning("No Processes", "Please add at least one process.")
            return

        algo = self.algo_var.get()
        try:
            if algo == "FCFS":        timeline = fcfs(self.processes)
            elif algo == "SJF":       timeline = sjf(self.processes)
            elif algo == "SRTF":      timeline = srtf(self.processes)
            elif algo == "Round Robin":
                q = int(self.quantum_var.get())
                if q < 1: raise ValueError
                timeline = round_robin(self.processes, q)
            elif algo == "Priority":  timeline = priority_sched(self.processes)
        except Exception as e:
            messagebox.showerror("Error", str(e)); return

        metrics = compute_metrics(self.processes, timeline)
        self._draw_gantt(timeline, algo)
        self._draw_metrics(metrics)
        self._draw_table(metrics)
        self.notebook.select(0)

    def _draw_gantt(self, timeline, title):
        for w in self.gantt_tab.winfo_children(): w.destroy()

        merged = merge_timeline(timeline)
        max_t  = max(e for _, _, e in merged)

        fig, ax = plt.subplots(figsize=(9, 2.4))
        fig.patch.set_facecolor(SURFACE)
        ax.set_facecolor(SURFACE)

        bar_h, bar_y = 0.5, 0.25
        for pid, s, e in merged:
            color = self.color_map.get(pid, PROC_COLORS[0])
            ax.barh(bar_y, e - s, left=s, height=bar_h,
                    color=color, edgecolor=BG, linewidth=1.2)
            if (e - s) >= 0.6:
                ax.text(s + (e-s)/2, bar_y, pid,
                        ha="center", va="center",
                        fontsize=9, fontweight="bold", color="white",
                        fontfamily="Consolas")

        ax.set_xlim(0, max_t)
        ax.set_xticks(range(0, max_t + 1))
        ax.tick_params(colors=TEXT2, labelsize=8)
        ax.set_yticks([bar_y]); ax.set_yticklabels(["CPU"], color=TEXT2, fontsize=9)
        ax.set_ylim(0, 1)
        ax.set_xlabel("Time units", color=TEXT2, fontsize=9)
        ax.set_title(f"{title} — Gantt Chart", color=TEXT, fontsize=11,
                     fontweight="bold", pad=8, fontfamily="Consolas")
        for spine in ax.spines.values(): spine.set_edgecolor(BORDER)
        ax.tick_params(axis="x", colors=TEXT2)
        ax.grid(axis="x", color=BORDER, linestyle="--", alpha=0.5)

        # Legend
        legend_patches = [
            mpatches.Patch(color=self.color_map.get(p["pid"], PROC_COLORS[0]),
                           label=p["pid"])
            for p in self.processes
        ]
        ax.legend(handles=legend_patches, loc="upper right",
                  fontsize=8, framealpha=0.2,
                  labelcolor=TEXT, facecolor=SURFACE2)

        plt.tight_layout(pad=1.0)
        canvas = FigureCanvasTkAgg(fig, master=self.gantt_tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)
        plt.close(fig)

    def _draw_metrics(self, metrics):
        for w in self.metrics_tab.winfo_children(): w.destroy()

        avg_wt  = round(sum(m["wt"]  for m in metrics) / len(metrics), 2)
        avg_tat = round(sum(m["tat"] for m in metrics) / len(metrics), 2)
        avg_rt  = round(sum(m["rt"]  for m in metrics) / len(metrics), 2)
        total_t = max(m["finish"] for m in metrics)
        busy_t  = sum(m["burst"] for m in metrics)
        util    = round(busy_t / total_t * 100, 1) if total_t else 0

        # Metric cards
        cards_frame = tk.Frame(self.metrics_tab, bg=BG)
        cards_frame.pack(fill="x", padx=12, pady=12)

        cards = [
            ("Avg Waiting Time",    f"{avg_wt}",   ACCENT),
            ("Avg Turnaround Time", f"{avg_tat}",  ACCENT2),
            ("Avg Response Time",   f"{avg_rt}",   SUCCESS),
            ("CPU Utilization",     f"{util}%",    WARNING),
        ]
        for label, value, color in cards:
            card = tk.Frame(cards_frame, bg=SURFACE, padx=16, pady=12)
            card.pack(side="left", fill="x", expand=True, padx=5)
            tk.Label(card, text=value, bg=SURFACE, fg=color,
                     font=("Consolas", 22, "bold")).pack(anchor="w")
            tk.Label(card, text=label, bg=SURFACE, fg=TEXT2,
                     font=("Consolas", 9)).pack(anchor="w")

        # Bar chart
        fig, axes = plt.subplots(1, 2, figsize=(9, 3.2))
        fig.patch.set_facecolor(SURFACE)

        pids   = [m["pid"] for m in metrics]
        colors = [self.color_map.get(m["pid"], PROC_COLORS[0]) for m in metrics]
        x = np.arange(len(pids))
        w = 0.25

        ax = axes[0]
        ax.set_facecolor(SURFACE)
        b1 = ax.bar(x - w, [m["wt"]  for m in metrics], w, label="Waiting",     color=ACCENT,  alpha=0.9)
        b2 = ax.bar(x,     [m["tat"] for m in metrics], w, label="Turnaround",  color=ACCENT2, alpha=0.9)
        b3 = ax.bar(x + w, [m["rt"]  for m in metrics], w, label="Response",    color=SUCCESS, alpha=0.9)
        ax.set_xticks(x); ax.set_xticklabels(pids, color=TEXT2, fontsize=9)
        ax.tick_params(colors=TEXT2)
        ax.set_ylabel("Time units", color=TEXT2, fontsize=9)
        ax.set_title("Per-Process Time Metrics", color=TEXT, fontsize=10,
                     fontweight="bold", fontfamily="Consolas")
        ax.legend(fontsize=8, labelcolor=TEXT, facecolor=SURFACE2, framealpha=0.3)
        for spine in ax.spines.values(): spine.set_edgecolor(BORDER)
        ax.grid(axis="y", color=BORDER, linestyle="--", alpha=0.4)

        ax2 = axes[1]
        ax2.set_facecolor(SURFACE)
        ax2.bar(pids, [m["burst"] for m in metrics], color=colors, alpha=0.9, width=0.5)
        ax2.set_title("Burst Time per Process", color=TEXT, fontsize=10,
                      fontweight="bold", fontfamily="Consolas")
        ax2.tick_params(colors=TEXT2)
        ax2.set_ylabel("Burst time", color=TEXT2, fontsize=9)
        for spine in ax2.spines.values(): spine.set_edgecolor(BORDER)
        ax2.grid(axis="y", color=BORDER, linestyle="--", alpha=0.4)

        plt.tight_layout(pad=1.2)
        canvas = FigureCanvasTkAgg(fig, master=self.metrics_tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=(0,8))
        plt.close(fig)

    def _draw_table(self, metrics):
        for w in self.table_tab.winfo_children(): w.destroy()

        cols = ("PID", "Arrival", "Burst", "Priority", "Start", "Finish",
                "Waiting", "Turnaround", "Response")
        tree = ttk.Treeview(self.table_tab, columns=cols, show="headings")
        widths = [60, 70, 60, 70, 60, 70, 70, 90, 80]
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")

        for m in metrics:
            tree.insert("", "end", values=(
                m["pid"], m["arrival"], m["burst"], m["priority"],
                m["start"], m["finish"], m["wt"], m["tat"], m["rt"]
            ))

        sb = ttk.Scrollbar(self.table_tab, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(fill="both", expand=True, padx=8, pady=8)

        # Summary row
        n = len(metrics)
        summary = tk.Frame(self.table_tab, bg=SURFACE, padx=14, pady=10)
        summary.pack(fill="x", padx=8, pady=(0,8))
        avg_wt  = round(sum(m["wt"]  for m in metrics)/n, 2)
        avg_tat = round(sum(m["tat"] for m in metrics)/n, 2)
        avg_rt  = round(sum(m["rt"]  for m in metrics)/n, 2)
        tk.Label(summary,
                 text=f"  Avg Waiting: {avg_wt}    Avg Turnaround: {avg_tat}    Avg Response: {avg_rt}",
                 bg=SURFACE, fg=ACCENT, font=("Consolas", 10, "bold")).pack(anchor="w")


if __name__ == "__main__":
    root = tk.Tk()
    app = CPUSchedulerApp(root)
    root.mainloop()
