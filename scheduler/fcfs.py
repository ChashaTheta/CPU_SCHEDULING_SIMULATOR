from typing import List
from .base import BaseScheduler, TimelineEntry
from .process import Process


class FCFSScheduler(BaseScheduler):
    """
    First Come First Served (FCFS) — Non-preemptive.

    Processes are executed in the order they arrive.
    Ties in arrival time are broken by PID (alphabetical).
    """

    def schedule(self) -> List[TimelineEntry]:
        self.timeline = []
        current_time = 0

        for proc in self._sorted_by_arrival():
            # CPU sits idle if the next process hasn't arrived yet
            if current_time < proc.arrival_time:
                current_time = proc.arrival_time

            start = current_time
            end   = current_time + proc.burst_time
            self.timeline.append((proc.pid, start, end))
            current_time = end

        return self.timeline
