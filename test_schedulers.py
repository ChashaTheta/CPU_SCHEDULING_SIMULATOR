"""
tests/test_schedulers.py
Unit tests for all five CPU scheduling algorithms.
Run: python -m pytest tests/ -v
  or python -m unittest discover -s tests -v
"""
import sys, os, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scheduler import (
    Process, FCFSScheduler, SJFScheduler, SRTFScheduler,
    RoundRobinScheduler, PriorityScheduler,
)

def make_procs():
    return [
        Process("P1", arrival_time=0, burst_time=6, priority=3),
        Process("P2", arrival_time=2, burst_time=4, priority=1),
        Process("P3", arrival_time=4, burst_time=2, priority=4),
        Process("P4", arrival_time=6, burst_time=5, priority=2),
    ]

def total_burst(procs):
    return sum(p.burst_time for p in procs)

# ── FCFS ──────────────────────────────────────────────────────────────
class TestFCFS(unittest.TestCase):
    def test_timeline_length(self):
        self.assertEqual(len(FCFSScheduler(make_procs()).schedule()), 4)

    def test_order_by_arrival(self):
        tl = FCFSScheduler(make_procs()).schedule()
        self.assertEqual([p for p,_,_ in tl], ["P1","P2","P3","P4"])

    def test_no_overlap(self):
        tl = FCFSScheduler(make_procs()).schedule()
        for i in range(len(tl)-1):
            self.assertLessEqual(tl[i][2], tl[i+1][1])

    def test_total_burst(self):
        procs = make_procs()
        tl = FCFSScheduler(procs).schedule()
        self.assertEqual(sum(e-s for _,s,e in tl), total_burst(procs))

    def test_metrics_non_negative(self):
        sch = FCFSScheduler(make_procs())
        sch.schedule()
        r = sch.summary()
        self.assertGreaterEqual(r["avg_waiting_time"], 0)
        self.assertGreater(r["cpu_utilization"], 0)

    def test_single_process(self):
        tl = FCFSScheduler([Process("P1",0,5)]).schedule()
        self.assertEqual(tl, [("P1",0,5)])

# ── SJF ───────────────────────────────────────────────────────────────
class TestSJF(unittest.TestCase):
    def test_shortest_chosen_first(self):
        procs = [
            Process("P1",0,6), Process("P2",2,4), Process("P3",4,2),
        ]
        pids = [p for p,_,_ in SJFScheduler(procs).schedule()]
        self.assertLess(pids.index("P3"), pids.index("P2"))

    def test_no_overlap(self):
        tl = SJFScheduler(make_procs()).schedule()
        for i in range(len(tl)-1):
            self.assertLessEqual(tl[i][2], tl[i+1][1])

    def test_total_burst(self):
        procs = make_procs()
        tl = SJFScheduler(procs).schedule()
        self.assertEqual(sum(e-s for _,s,e in tl), total_burst(procs))

# ── SRTF ──────────────────────────────────────────────────────────────
class TestSRTF(unittest.TestCase):
    def test_preemption_happens(self):
        procs = [Process("P1",0,8), Process("P2",1,2)]
        tl = SRTFScheduler(procs).schedule()
        p1_segs = [x for x in tl if x[0]=="P1"]
        self.assertGreaterEqual(len(p1_segs), 2)

    def test_total_burst(self):
        procs = make_procs()
        tl = SRTFScheduler(procs).schedule()
        pid_b = {}
        for pid,s,e in tl: pid_b[pid] = pid_b.get(pid,0) + (e-s)
        for p in procs: self.assertEqual(pid_b[p.pid], p.burst_time)

    def test_no_overlap(self):
        tl = SRTFScheduler(make_procs()).schedule()
        for i in range(len(tl)-1):
            self.assertLessEqual(tl[i][2], tl[i+1][1])

# ── Round Robin ───────────────────────────────────────────────────────
class TestRoundRobin(unittest.TestCase):
    def test_invalid_quantum(self):
        with self.assertRaises(ValueError):
            RoundRobinScheduler(make_procs(), quantum=0)

    def test_quantum_respected(self):
        q = 2
        tl = RoundRobinScheduler(make_procs(), quantum=q).schedule()
        for _,s,e in tl: self.assertLessEqual(e-s, q)

    def test_total_burst(self):
        procs = make_procs()
        tl = RoundRobinScheduler(procs, quantum=3).schedule()
        pid_b = {}
        for pid,s,e in tl: pid_b[pid] = pid_b.get(pid,0) + (e-s)
        for p in procs: self.assertEqual(pid_b[p.pid], p.burst_time)

    def test_large_quantum_equals_fcfs(self):
        procs = make_procs()
        fcfs = [p for p,_,_ in FCFSScheduler(procs).schedule()]
        rr   = [p for p,_,_ in RoundRobinScheduler(procs, quantum=100).schedule()]
        self.assertEqual(fcfs, rr)

# ── Priority ──────────────────────────────────────────────────────────
class TestPriority(unittest.TestCase):
    def test_highest_priority_first(self):
        procs = [
            Process("P1",0,3,priority=3),
            Process("P2",0,3,priority=1),
            Process("P3",0,3,priority=2),
        ]
        tl = PriorityScheduler(procs).schedule()
        self.assertEqual(tl[0][0], "P2")

    def test_total_burst(self):
        procs = make_procs()
        tl = PriorityScheduler(procs).schedule()
        pid_b = {}
        for pid,s,e in tl: pid_b[pid] = pid_b.get(pid,0) + (e-s)
        for p in procs: self.assertEqual(pid_b[p.pid], p.burst_time)

    def test_no_overlap(self):
        tl = PriorityScheduler(make_procs()).schedule()
        for i in range(len(tl)-1):
            self.assertLessEqual(tl[i][2], tl[i+1][1])

# ── Process dataclass ─────────────────────────────────────────────────
class TestProcess(unittest.TestCase):
    def test_compute_metrics(self):
        p = Process("P1", 0, 5)
        p.start_time = 0; p.finish_time = 5
        p.compute_metrics()
        self.assertEqual(p.turnaround_time, 5)
        self.assertEqual(p.waiting_time,    0)
        self.assertEqual(p.response_time,   0)

    def test_reset(self):
        p = Process("P1", 0, 5)
        p.start_time = 0; p.finish_time = 5
        p.compute_metrics()
        p.reset()
        self.assertIsNone(p.waiting_time)
        self.assertIsNone(p.turnaround_time)

if __name__ == "__main__":
    unittest.main()
