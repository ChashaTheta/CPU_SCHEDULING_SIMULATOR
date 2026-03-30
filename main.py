
"""
main.py — Interactive CLI for the CPU Scheduler Simulator
----------------------------------------------------------
Run:
    python main.py                  # interactive mode
    python main.py --demo           # run the built-in demo
    python main.py --compare        # compare all algorithms side-by-side
    python main.py --save gantt.png # save gantt chart instead of showing it
"""

import argparse
import sys
from tabulate import tabulate

from scheduler import (
    Process,
    FCFSScheduler,
    SJFScheduler,
    SRTFScheduler,
    RoundRobinScheduler,
    PriorityScheduler,
)
from visualizer import plot_gantt, plot_metrics


# ── Demo dataset ───────────────────────────────────────────────────────

DEMO_PROCESSES = [
    Process("P1", arrival_time=0, burst_time=6, priority=3),
    Process("P2", arrival_time=2, burst_time=4, priority=1),
    Process("P3", arrival_time=4, burst_time=2, priority=4),
    Process("P4", arrival_time=6, burst_time=5, priority=2),
    Process("P5", arrival_time=8, burst_time=3, priority=5),
]


# ── Pretty printers ────────────────────────────────────────────────────

def print_timeline(timeline):
    rows = [(pid, start, end, end - start) for pid, start, end in timeline]
    print(tabulate(rows, headers=["PID", "Start", "End", "Duration"],
                   tablefmt="rounded_outline"))


def print_summary(summary):
    procs = summary["processes"]
    rows  = [
        (
            p.pid,
            p.arrival_time,
            p.burst_time,
            p.priority,
            p.start_time,
            p.finish_time,
            p.waiting_time,
            p.turnaround_time,
            p.response_time,
        )
        for p in procs
    ]
    print(tabulate(
        rows,
        headers=["PID", "Arrival", "Burst", "Priority",
                 "Start", "Finish", "Wait", "Turnaround", "Response"],
        tablefmt="rounded_outline",
    ))
    print(f"\n  Avg Waiting Time    : {summary['avg_waiting_time']}")
    print(f"  Avg Turnaround Time : {summary['avg_turnaround_time']}")
    print(f"  Avg Response Time   : {summary['avg_response_time']}")
    print(f"  CPU Utilisation     : {summary['cpu_utilization']}%")


# ── Input helpers ──────────────────────────────────────────────────────

def input_int(prompt, min_val=0, max_val=9999):
    while True:
        try:
            val = int(input(prompt))
            if min_val <= val <= max_val:
                return val
            print(f"  Please enter a value between {min_val} and {max_val}.")
        except ValueError:
            print("  Invalid input — please enter an integer.")


def collect_processes():
    print("\n── Process Input ──────────────────────────────────────")
    n = input_int("How many processes? (1–20): ", 1, 20)
    procs = []
    for i in range(1, n + 1):
        print(f"\n  Process P{i}")
        arrival  = input_int("    Arrival time  : ", 0)
        burst    = input_int("    Burst time    : ", 1)
        priority = input_int("    Priority (1=highest): ", 1, 99)
        procs.append(Process(f"P{i}", arrival, burst, priority))
    return procs


def choose_algorithm(procs):
    menu = {
        "1": ("FCFS",     lambda: FCFSScheduler(procs)),
        "2": ("SJF",      lambda: SJFScheduler(procs)),
        "3": ("SRTF",     lambda: SRTFScheduler(procs)),
        "4": ("Round Robin", None),
        "5": ("Priority", lambda: PriorityScheduler(procs)),
        "6": ("Compare all", None),
    }
    print("\n── Choose Algorithm ────────────────────────────────────")
    for k, (name, _) in menu.items():
        print(f"  {k}. {name}")

    choice = ""
    while choice not in menu:
        choice = input("Enter choice: ").strip()

    name, factory = menu[choice]

    if choice == "4":
        q = input_int("  Time quantum: ", 1, 100)
        factory = lambda: RoundRobinScheduler(procs, quantum=q)

    return name, factory, choice == "6"


# ── Run modes ──────────────────────────────────────────────────────────

def run_single(scheduler, title, save_path=None):
    timeline = scheduler.schedule()
    summary  = scheduler.summary()

    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")
    print("\nGantt Timeline:")
    print_timeline(timeline)
    print("\nProcess Details:")
    print_summary(summary)

    plot_gantt(
        timeline,
        title=title,
        save_path=save_path,
        show=(save_path is None),
    )


def run_compare(procs, quantum=2, save_path=None):
    algorithms = [
        ("FCFS",         FCFSScheduler(procs)),
        ("SJF",          SJFScheduler(procs)),
        ("SRTF",         SRTFScheduler(procs)),
        (f"RR(q={quantum})", RoundRobinScheduler(procs, quantum=quantum)),
        ("Priority",     PriorityScheduler(procs)),
    ]

    summaries = []
    for name, sched in algorithms:
        sched.schedule()
        s = sched.summary()
        s["algorithm"] = name
        summaries.append(s)

    # Print comparison table
    rows = [
        (s["algorithm"], s["avg_waiting_time"],
         s["avg_turnaround_time"], s["avg_response_time"],
         f"{s['cpu_utilization']}%")
        for s in summaries
    ]
    print(f"\n{'='*65}")
    print("  Algorithm Comparison")
    print(f"{'='*65}")
    print(tabulate(rows,
                   headers=["Algorithm", "Avg Wait", "Avg TAT", "Avg RT", "CPU Util"],
                   tablefmt="rounded_outline"))

    plot_metrics(summaries, save_path=save_path, show=(save_path is None))


# ── Entry point ────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CPU Scheduler Simulator")
    parser.add_argument("--demo",    action="store_true", help="Run with demo processes")
    parser.add_argument("--compare", action="store_true", help="Compare all algorithms")
    parser.add_argument("--save",    metavar="PATH",      help="Save chart to file instead of displaying")
    args = parser.parse_args()

    print("╔══════════════════════════════════════════╗")
    print("║   CPU Scheduler Simulator  (Python)      ║")
    print("╚══════════════════════════════════════════╝")

    if args.demo or args.compare:
        procs = DEMO_PROCESSES
        print("\nUsing demo processes:")
        rows = [(p.pid, p.arrival_time, p.burst_time, p.priority) for p in procs]
        print(tabulate(rows, headers=["PID", "Arrival", "Burst", "Priority"],
                       tablefmt="rounded_outline"))

        if args.compare:
            run_compare(procs, save_path=args.save)
        else:
            run_compare(procs, save_path=args.save)
        return

    # Interactive mode
    procs = collect_processes()
    name, factory, compare_all = choose_algorithm(procs)

    if compare_all:
        q = input_int("  Time quantum for RR: ", 1, 100)
        run_compare(procs, quantum=q, save_path=args.save)
    else:
        run_single(factory(), title=name, save_path=args.save)


if __name__ == "__main__":
    main()
