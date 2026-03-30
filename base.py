from abc import ABC, abstractmethod
from typing import List, Tuple
import copy

from .process import Process


# A timeline entry: (pid, start_time, end_time)
TimelineEntry = Tuple[str, int, int]


class BaseScheduler(ABC):
    """Abstract base class for all CPU scheduling algorithms."""

    def __init__(self, processes: List[Process]):
        # Deep-copy so original list is never mutated
        self.processes: List[Process] = copy.deepcopy(processes)
        self.timeline: List[TimelineEntry] = []

    @abstractmethod
    def schedule(self) -> List[TimelineEntry]:
        """Run the scheduling algorithm and return a Gantt timeline."""
        ...

    def compute_all_metrics(self) -> List[Process]:
        """
        Walk the timeline once to assign start / finish times,
        then call compute_metrics() on every process.
        """
        # Build per-process first-start and last-finish from the timeline
        first_start: dict[str, int] = {}
        last_finish: dict[str, int] = {}

        for pid, start, end in self.timeline:
            if pid not in first_start:
                first_start[pid] = start
            last_finish[pid] = end

        for proc in self.processes:
            if proc.pid in first_start:
                proc.start_time = first_start[proc.pid]
                proc.finish_time = last_finish[proc.pid]
                proc.compute_metrics()

        return self.processes

    # ------------------------------------------------------------------
    # Shared helper utilities
    # ------------------------------------------------------------------

    def _sorted_by_arrival(self) -> List[Process]:
        return sorted(self.processes, key=lambda p: (p.arrival_time, p.pid))

    @staticmethod
    def avg(values) -> float:
        return round(sum(values) / len(values), 2) if values else 0.0

    def summary(self) -> dict:
        """Return a dict of average metrics after scheduling."""
        procs = self.compute_all_metrics()
        wt  = [p.waiting_time    for p in procs if p.waiting_time    is not None]
        tat = [p.turnaround_time for p in procs if p.turnaround_time is not None]
        rt  = [p.response_time   for p in procs if p.response_time   is not None]
        total_time = max((e for _, _, e in self.timeline), default=0)
        busy_time  = sum(p.burst_time for p in procs)
        cpu_util   = round((busy_time / total_time * 100), 2) if total_time else 0.0

        return {
            "algorithm": self.__class__.__name__,
            "avg_waiting_time": self.avg(wt),
            "avg_turnaround_time": self.avg(tat),
            "avg_response_time": self.avg(rt),
            "cpu_utilization": cpu_util,
            "processes": procs,
        }
