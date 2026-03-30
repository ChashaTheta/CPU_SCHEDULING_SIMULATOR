# CPU Scheduler Simulator

A Python simulator for five classic CPU scheduling algorithms with real-time Gantt chart visualisations and performance metrics.

## Algorithms Implemented

| Algorithm | Type | Key property |
|-----------|------|-------------|
| FCFS | Non-preemptive | Processes run in arrival order |
| SJF | Non-preemptive | Shortest burst time chosen from ready queue |
| SRTF | Preemptive | Shortest *remaining* time preempts the CPU |
| Round Robin | Preemptive | Each process gets a fixed time quantum |
| Priority | Preemptive | Lowest priority number runs first (optional aging) |

## Project Structure

```
cpu_scheduler/
├── main.py                  # CLI entry point
├── requirements.txt
├── scheduler/
│   ├── __init__.py
│   ├── process.py           # Process dataclass
│   ├── base.py              # Abstract base scheduler
│   ├── fcfs.py              # FCFS algorithm
│   ├── sjf.py               # SJF + SRTF algorithms
│   ├── round_robin.py       # Round Robin algorithm
│   └── priority.py          # Priority algorithm
├── visualizer/
│   ├── __init__.py
│   ├── gantt.py             # Gantt chart (matplotlib)
│   └── metrics.py           # Metrics comparison bar chart
└── tests/
    └── test_schedulers.py   # pytest unit tests
```

## Setup

```bash
# Clone the repo
git clone https://github.com/<your-username>/cpu-scheduler-simulator.git
cd cpu-scheduler-simulator

# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Demo mode (built-in processes, compare all algorithms)
```bash
python main.py --demo
```

### Interactive mode (enter your own processes)
```bash
python main.py
```

### Save chart to a file instead of displaying
```bash
python main.py --demo --save gantt.png
```

### Run unit tests
```bash
python -m pytest tests/ -v
```

## Example Output

```
╔══════════════════════════════════════════╗
║   CPU Scheduler Simulator  (Python)      ║
╚══════════════════════════════════════════╝

Algorithm Comparison
╭─────────────┬──────────┬─────────┬─────────┬──────────╮
│ Algorithm   │ Avg Wait │ Avg TAT │ Avg RT  │ CPU Util │
├─────────────┼──────────┼─────────┼─────────┼──────────┤
│ FCFS        │ 5.6      │ 11.0    │ 5.6     │ 100.0%   │
│ SJF         │ 4.2      │ 9.6     │ 4.2     │ 100.0%   │
│ SRTF        │ 3.4      │ 8.8     │ 1.4     │ 100.0%   │
│ RR(q=2)     │ 5.8      │ 11.2    │ 2.0     │ 100.0%   │
│ Priority    │ 4.6      │ 10.0    │ 2.6     │ 100.0%   │
╰─────────────┴──────────┴─────────┴─────────┴──────────╯
```

## Metrics Explained

- **Waiting Time** = Turnaround Time − Burst Time
- **Turnaround Time** = Finish Time − Arrival Time
- **Response Time** = First CPU Time − Arrival Time
- **CPU Utilisation** = Total Burst Time / Total Elapsed Time × 100



