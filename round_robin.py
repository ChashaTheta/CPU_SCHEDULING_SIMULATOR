from typing import List
from collections import deque
from .base import BaseScheduler, TimelineEntry
from .process import Process
import copy


class RoundRobinScheduler(BaseScheduler):
    """
    Round Robin (RR) — Preemptive with fixed time quantum.

    Each process is given at most `quantum` time units per turn.
    Processes that exhaust their quantum are re-queued; newly
    arrived processes join the queue before re-queued ones.

    Parameters
    ----------
    processes : list of Process
    quantum   : int, time slice in time units (default 2)
    """

    def __init__(self, processes: List[Process], quantum: int = 2):
        super().__init__(processes)
        if quantum < 1:
            raise ValueError("Quantum must be at least 1.")
        self.quantum = quantum

    def schedule(self) -> List[TimelineEntry]:
        self.timeline = []

        # Sort a working copy by arrival time
        pool = sorted(
            copy.deepcopy(self.processes),
            key=lambda p: (p.arrival_time, p.pid),
        )
        remaining = {p.pid: p.burst_time for p in pool}
        arrivals  = {p.pid: p.arrival_time for p in pool}

        queue: deque = deque()
        pool_idx = 0          # pointer into the sorted pool list
        current_time = 0

        # Seed queue with processes that arrive at t=0
        while pool_idx < len(pool) and pool[pool_idx].arrival_time <= current_time:
            queue.append(pool[pool_idx].pid)
            pool_idx += 1

        visited = set()

        while queue:
            pid = queue.popleft()

            run = min(self.quantum, remaining[pid])
            start = current_time
            end   = current_time + run
            self.timeline.append((pid, start, end))
            current_time = end
            remaining[pid] -= run

            # Enqueue newly arrived processes during this slice
            while pool_idx < len(pool) and pool[pool_idx].arrival_time <= current_time:
                queue.append(pool[pool_idx].pid)
                pool_idx += 1

            # Re-queue if still has burst left
            if remaining[pid] > 0:
                queue.append(pid)

            # If queue is empty but processes remain, jump to next arrival
            if not queue and pool_idx < len(pool):
                current_time = pool[pool_idx].arrival_time
                while pool_idx < len(pool) and pool[pool_idx].arrival_time <= current_time:
                    queue.append(pool[pool_idx].pid)
                    pool_idx += 1

        return self.timeline
