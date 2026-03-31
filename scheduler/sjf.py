from typing import List
from .base import BaseScheduler, TimelineEntry
from .process import Process
import copy


class SJFScheduler(BaseScheduler):
    """
    Shortest Job First (SJF) — Non-preemptive.

    At each scheduling point the available process with the
    smallest burst time is selected.  Ties are broken by arrival
    time, then PID.
    """

    def schedule(self) -> List[TimelineEntry]:
        self.timeline = []
        remaining = copy.deepcopy(self.processes)
        current_time = 0

        while remaining:
            available = [p for p in remaining if p.arrival_time <= current_time]

            if not available:
                # Jump forward to the next arriving process
                current_time = min(p.arrival_time for p in remaining)
                continue

            # Pick shortest burst; break ties by arrival then PID
            chosen = min(available, key=lambda p: (p.burst_time, p.arrival_time, p.pid))
            remaining.remove(chosen)

            start = current_time
            end   = current_time + chosen.burst_time
            self.timeline.append((chosen.pid, start, end))
            current_time = end

        return self.timeline


class SRTFScheduler(BaseScheduler):
    """
    Shortest Remaining Time First (SRTF) — Preemptive SJF.

    At every clock tick the ready process with the smallest
    remaining burst time preempts the CPU.  Consecutive ticks
    for the same process are merged into a single timeline entry.
    """

    def schedule(self) -> List[TimelineEntry]:
        self.timeline = []
        procs = [(p.pid, p.arrival_time, p.burst_time, p.burst_time) for p in self.processes]
        # (pid, arrival, original_burst, remaining)

        remaining = {p.pid: p.burst_time for p in self.processes}
        arrivals  = {p.pid: p.arrival_time for p in self.processes}

        total_time = (
            max(p.arrival_time for p in self.processes)
            + sum(p.burst_time for p in self.processes)
            + 1
        )

        current_pid = None
        seg_start   = 0
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

            # Preempt to shortest remaining; ties broken by PID
            chosen = min(ready, key=lambda pid: (remaining[pid], pid))

            if chosen != current_pid:
                if current_pid is not None:
                    self.timeline.append((current_pid, seg_start, t))
                current_pid = chosen
                seg_start   = t

            remaining[chosen] -= 1
            t += 1

            if remaining[chosen] == 0:
                self.timeline.append((chosen, seg_start, t))
                del remaining[chosen]
                current_pid = None

            if not remaining:
                break

        return self.timeline
