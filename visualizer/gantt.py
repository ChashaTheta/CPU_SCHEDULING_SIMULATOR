"""
visualizer/gantt.py
-------------------
Renders a colour-coded Gantt chart for a scheduler timeline
using Matplotlib.  No external data files required.
"""

from typing import List, Tuple
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import MaxNLocator


# 10 visually distinct colours (cycles if more than 10 processes)
PROCESS_COLORS = [
    "#3266AD", "#0F6E56", "#D85A30", "#993556",
    "#BA7517", "#3B6D11", "#533AB7", "#A32D2D",
    "#185FA5", "#633806",
]


def _merge_timeline(timeline: List[Tuple[str, int, int]]) -> List[Tuple[str, int, int]]:
    """Merge consecutive same-PID entries into one bar."""
    merged = []
    for pid, start, end in timeline:
        if merged and merged[-1][0] == pid and merged[-1][2] == start:
            merged[-1] = (pid, merged[-1][1], end)
        else:
            merged.append([pid, start, end])
    return [(p, s, e) for p, s, e in merged]


def plot_gantt(
    timeline: List[Tuple[str, int, int]],
    title: str = "Gantt Chart",
    save_path: str = None,
    show: bool = True,
) -> plt.Figure:
    """
    Draw a horizontal Gantt chart.

    Parameters
    ----------
    timeline  : list of (pid, start, end)
    title     : chart title string
    save_path : if given, save figure to this file path
    show      : call plt.show() when True

    Returns
    -------
    matplotlib Figure
    """
    merged = _merge_timeline(timeline)

    # Collect unique PIDs to assign consistent colours
    unique_pids = list(dict.fromkeys(pid for pid, _, _ in timeline))
    color_map   = {pid: PROCESS_COLORS[i % len(PROCESS_COLORS)]
                   for i, pid in enumerate(unique_pids)}

    fig, ax = plt.subplots(figsize=(max(10, len(merged) * 0.8), 3.5))
    fig.patch.set_facecolor("#F8F8F6")
    ax.set_facecolor("#F8F8F6")

    bar_height = 0.5
    bar_y      = 0.25   # centre of the single row

    for pid, start, end in merged:
        width = end - start
        color = color_map[pid]

        ax.barh(
            bar_y, width, left=start,
            height=bar_height, color=color,
            edgecolor="white", linewidth=0.8,
        )
        # Label each block if wide enough
        if width >= 0.8:
            ax.text(
                start + width / 2, bar_y,
                pid,
                ha="center", va="center",
                fontsize=9, fontweight="bold", color="white",
            )

    # X-axis ticks at every integer time unit
    max_time = max(end for _, _, end in merged)
    ax.set_xlim(0, max_time)
    ax.set_xticks(range(0, max_time + 1))
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xlabel("Time units", fontsize=10)

    # Hide y-axis; show only "CPU" label
    ax.set_yticks([bar_y])
    ax.set_yticklabels(["CPU"])
    ax.set_ylim(0, 1)

    # Legend
    patches = [
        mpatches.Patch(color=color_map[pid], label=pid)
        for pid in unique_pids
    ]
    ax.legend(
        handles=patches,
        loc="upper right",
        fontsize=9,
        framealpha=0.9,
        ncol=min(len(unique_pids), 6),
    )

    ax.set_title(title, fontsize=12, fontweight="bold", pad=10)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", linestyle="--", alpha=0.4)

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[Gantt] Saved to {save_path}")

    if show:
        plt.show()

    return fig
