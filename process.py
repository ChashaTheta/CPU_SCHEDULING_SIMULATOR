from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Process:
    """Represents a single process in the CPU scheduler."""
    pid: str
    arrival_time: int
    burst_time: int
    priority: int = 1

    # Computed fields (filled after scheduling)
    start_time: Optional[int] = field(default=None, repr=False)
    finish_time: Optional[int] = field(default=None, repr=False)
    waiting_time: Optional[int] = field(default=None, repr=False)
    turnaround_time: Optional[int] = field(default=None, repr=False)
    response_time: Optional[int] = field(default=None, repr=False)

    def compute_metrics(self):
        """Calculate waiting, turnaround, and response time after scheduling."""
        if self.finish_time is not None and self.start_time is not None:
            self.turnaround_time = self.finish_time - self.arrival_time
            self.waiting_time = self.turnaround_time - self.burst_time
            self.response_time = self.start_time - self.arrival_time

    def reset(self):
        """Reset all computed fields so the process can be re-scheduled."""
        self.start_time = None
        self.finish_time = None
        self.waiting_time = None
        self.turnaround_time = None
        self.response_time = None

    def __repr__(self):
        return (
            f"Process(pid={self.pid!r}, arrival={self.arrival_time}, "
            f"burst={self.burst_time}, priority={self.priority})"
        )
