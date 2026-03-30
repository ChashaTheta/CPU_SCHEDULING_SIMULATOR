"""
visualizer/metrics.py
---------------------
Bar-chart comparison of performance metrics across multiple
scheduling algorithms.
"""

from typing import List, Dict
import matplotlib.pyplot as plt
import numpy as np


def plot_metrics(
    summaries: List[Dict],
    save_path: str = None,
    show: bool = True,
) -> plt.Figure:
    """
    Compare avg waiting time, avg turnaround time, avg response time,
    and CPU utilisation across several algorithm runs.

    Parameters
    ----------
    summaries  : list of dicts returned by BaseScheduler.summary()
    save_path  : optional file path to save the figure
    show       : call plt.show() when True
    """
    labels     = [s["algorithm"] for s in summaries]
    avg_wt     = [s["avg_waiting_time"]    for s in summaries]
    avg_tat    = [s["avg_turnaround_time"] for s in summaries]
    avg_rt     = [s["avg_response_time"]   for s in summaries]
    cpu_util   = [s["cpu_utilization"]     for s in summaries]

    x     = np.arange(len(labels))
    width = 0.2

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    fig.patch.set_facecolor("#F8F8F6")

    # ── Left plot: time-based metrics ──────────────────────────────────
    ax = axes[0]
    ax.set_facecolor("#F8F8F6")
    b1 = ax.bar(x - width, avg_wt,  width, label="Avg Waiting",     color="#3266AD")
    b2 = ax.bar(x,          avg_tat, width, label="Avg Turnaround",  color="#0F6E56")
    b3 = ax.bar(x + width, avg_rt,  width, label="Avg Response",    color="#D85A30")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=15, ha="right", fontsize=9)
    ax.set_ylabel("Time units", fontsize=9)
    ax.set_title("Time Metrics by Algorithm", fontsize=11, fontweight="bold")
    ax.legend(fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    for bars in (b1, b2, b3):
        for bar in bars:
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2, h + 0.05,
                f"{h:.1f}", ha="center", va="bottom", fontsize=7,
            )

    # ── Right plot: CPU utilisation ────────────────────────────────────
    ax2 = axes[1]
    ax2.set_facecolor("#F8F8F6")
    bars = ax2.bar(labels, cpu_util, color="#533AB7", width=0.45)

    ax2.set_ylabel("CPU Utilisation (%)", fontsize=9)
    ax2.set_title("CPU Utilisation by Algorithm", fontsize=11, fontweight="bold")
    ax2.set_ylim(0, 110)
    ax2.spines[["top", "right"]].set_visible(False)
    ax2.grid(axis="y", linestyle="--", alpha=0.4)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, rotation=15, ha="right", fontsize=9)

    for bar in bars:
        h = bar.get_height()
        ax2.text(
            bar.get_x() + bar.get_width() / 2, h + 1,
            f"{h:.1f}%", ha="center", va="bottom", fontsize=8,
        )

    plt.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"[Metrics] Saved to {save_path}")

    if show:
        plt.show()

    return fig
