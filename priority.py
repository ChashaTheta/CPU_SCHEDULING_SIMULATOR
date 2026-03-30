from typing import List
from .base import BaseScheduler, TimelineEntry
from .process import Process
import copy


class PriorityScheduler(BaseScheduler):
    """
    Priority Scheduling — Preemptive.

    Lower priority number = higher priority (1 is highest).
    At every clock tick the ready process with the best (lowest)
    priority number preempts the CPU.  Consecutive ticks for the
    same process are merged into a single timeline entry.

    To avoid starvation a simple aging mechanism can optionally
    be enabled: waiting processes gain +1 effective priority
    every `aging_interval` ticks.

    Parameters
    ----------
    processes        : list of Process
    aging_interval   : int or None.  None disables aging (default).
    """

    def __init__(self, processes: List[Process], aging_interval=None):
        super().__init__(processes)
        self.aging_interval = aging_interval

    def schedule(self) -> List[TimelineEntry]:
        self.timeline = []

        remaining  = {p.pid: p.burst_time  for p in self.processes}
        arrivals   = {p.pid: p.arrival_time for p in self.processes}
        priorities = {p.pid: p.priority     for p in self.processes}
        eff_prio   = dict(priorities)          # effective priority (with aging)

        total_time = (
            max(p.arrival_time for p in self.processes)
            + sum(p.burst_time  for p in self.processes)
            + 1
        )

        current_pid = None
        seg_start   = 0
        waiting_since: dict[str, int] = {}     # track when a process started waiting
        t = 0

        while t < total_time:
            ready = [
                pid for pid, rem in remaining.items()
                if rem > 0 and arrivals[pid] <= t
            ]

            if not ready:
                if current_pid is not None:
                    self.timeline.append((current_pid, seg_start, t))
                    current_pid = None
                t += 1
                continue

            # Aging: boost priority of long-waiting processes
            if self.aging_interval:
                for pid in ready:
                    if pid not in waiting_since:
                        waiting_since[pid] = t
                    waited = t - waiting_since[pid]
                    boost  = waited // self.aging_interval
                    eff_prio[pid] = max(1, priorities[pid] - boost)

            chosen = min(ready, key=lambda pid: (eff_prio[pid], arrivals[pid], pid))

            if chosen != current_pid:
                if current_pid is not None:
                    self.timeline.append((current_pid, seg_start, t))
                    waiting_since[current_pid] = t   # reset for re-entry
                current_pid = chosen
                seg_start   = t
                waiting_since.pop(chosen, None)       # running ≠ waiting

            remaining[chosen] -= 1
            t += 1

            if remaining[chosen] == 0:
                self.timeline.append((chosen, seg_start, t))
                del remaining[chosen]
                current_pid = None

            if not remaining:
                break

        return self.timeline
