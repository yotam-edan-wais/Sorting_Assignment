# -*- coding: utf-8 -*-
"""
run_experiments.py
Data Structures – Sorting Algorithm Comparison
Spring 2026

Usage examples:
  python run_experiments.py                         # run default full experiment
  python run_experiments.py -a 1 2 5 -s 100 500 3000 -e 1 -r 20
  python run_experiments.py -a 3 4 5 -s 100 1000 10000 -e 2 -r 5
"""

import argparse
import random
import time
import sys
import io

# Force UTF-8 output on Windows so box-drawing characters work
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")          # non-interactive backend (works without a display)
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# ---------------------------------------------------------------------------
# ─── SORTING ALGORITHMS ────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def bubble_sort(arr):
    """Bubble Sort – O(n²) average / worst case."""
    a = arr.copy()
    n = len(a)
    for i in range(n):
        swapped = False
        for j in range(0, n - i - 1):
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                swapped = True
        if not swapped:          # already sorted – early exit
            break
    return a


def selection_sort(arr):
    """Selection Sort – O(n²) in all cases."""
    a = arr.copy()
    n = len(a)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if a[j] < a[min_idx]:
                min_idx = j
        a[i], a[min_idx] = a[min_idx], a[i]
    return a


def insertion_sort(arr):
    """Insertion Sort – O(n²) average/worst, O(n) best."""
    a = arr.copy()
    for i in range(1, len(a)):
        key = a[i]
        j = i - 1
        while j >= 0 and a[j] > key:
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = key
    return a


def merge_sort(arr):
    """Merge Sort – O(n log n) guaranteed."""
    a = arr.copy()
    _merge_sort_inplace(a, 0, len(a) - 1)
    return a


def _merge_sort_inplace(a, left, right):
    if left < right:
        mid = (left + right) // 2
        _merge_sort_inplace(a, left, mid)
        _merge_sort_inplace(a, mid + 1, right)
        _merge(a, left, mid, right)


def _merge(a, left, mid, right):
    L = a[left : mid + 1]
    R = a[mid + 1 : right + 1]
    i = j = 0
    k = left
    while i < len(L) and j < len(R):
        if L[i] <= R[j]:
            a[k] = L[i]; i += 1
        else:
            a[k] = R[j]; j += 1
        k += 1
    while i < len(L):
        a[k] = L[i]; i += 1; k += 1
    while j < len(R):
        a[k] = R[j]; j += 1; k += 1


def quick_sort(arr):
    """Quick Sort – O(n log n) average, O(n²) worst (randomised pivot)."""
    a = arr.copy()
    _quick_sort(a, 0, len(a) - 1)
    return a


def _quick_sort(a, low, high):
    if low < high:
        pi = _partition(a, low, high)
        _quick_sort(a, low, pi - 1)
        _quick_sort(a, pi + 1, high)


def _partition(a, low, high):
    # Randomised pivot to avoid worst-case on sorted input
    rand_idx = random.randint(low, high)
    a[rand_idx], a[high] = a[high], a[rand_idx]
    pivot = a[high]
    i = low - 1
    for j in range(low, high):
        if a[j] <= pivot:
            i += 1
            a[i], a[j] = a[j], a[i]
    a[i + 1], a[high] = a[high], a[i + 1]
    return i + 1


# ---------------------------------------------------------------------------
# ─── ALGORITHM REGISTRY ────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

ALGORITHM_MAP = {
    1: ("Bubble Sort",     bubble_sort),
    2: ("Selection Sort",  selection_sort),
    3: ("Insertion Sort",  insertion_sort),
    4: ("Merge Sort",      merge_sort),
    5: ("Quick Sort",      quick_sort),
}

# Colour palette (colour-blind friendly)
COLOURS = ["#E63946", "#457B9D", "#2A9D8F", "#E9C46A", "#F4A261"]

# ---------------------------------------------------------------------------
# ─── ARRAY GENERATORS ──────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def random_array(size, lo=0, hi=10_000_000):
    """Uniformly random integers."""
    return [random.randint(lo, hi) for _ in range(size)]


def nearly_sorted_array(size, noise_fraction, lo=0, hi=10_000_000):
    """
    Start with a sorted array and randomly swap a fraction of elements.
    noise_fraction=0.05 → swap 5 % of elements (by count of swaps).
    """
    arr = list(range(size))          # perfectly sorted 0..size-1
    n_swaps = max(1, int(size * noise_fraction))
    for _ in range(n_swaps):
        i, j = random.randrange(size), random.randrange(size)
        arr[i], arr[j] = arr[j], arr[i]
    return arr

# ---------------------------------------------------------------------------
# ─── TIMING HELPERS ────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

# Cap slow algorithms so the script doesn't run forever
MAX_SECONDS_PER_TIMING = 300   # 5 min safety cap (won't be hit normally)

SKIP_THRESHOLD_SECONDS = 30    # if avg time exceeds this, skip larger sizes


def time_algorithm(sort_fn, arr):
    """Return elapsed seconds for one sort."""
    start = time.perf_counter()
    sort_fn(arr)
    return time.perf_counter() - start


def run_timing(sort_fn, size, repetitions, array_gen, **gen_kwargs):
    """
    Run *sort_fn* on *repetitions* fresh arrays of *size* elements.
    Returns (mean_seconds, std_seconds).
    """
    times = []
    for _ in range(repetitions):
        arr = array_gen(size, **gen_kwargs)
        t = time_algorithm(sort_fn, arr)
        times.append(t)
    return float(np.mean(times)), float(np.std(times))

# ---------------------------------------------------------------------------
# ─── PLOTTING HELPERS ──────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

STYLE = {
    "figure.facecolor":  "#0f1117",
    "axes.facecolor":    "#161b22",
    "axes.edgecolor":    "#30363d",
    "axes.labelcolor":   "#c9d1d9",
    "xtick.color":       "#8b949e",
    "ytick.color":       "#8b949e",
    "text.color":        "#c9d1d9",
    "grid.color":        "#21262d",
    "grid.linewidth":    0.8,
    "legend.facecolor":  "#161b22",
    "legend.edgecolor":  "#30363d",
    "font.family":       "monospace",
}


def _apply_style():
    plt.rcParams.update(STYLE)


def _human_size(n):
    if n >= 1_000_000:
        return f"{n//1_000_000}M"
    if n >= 1_000:
        return f"{n//1_000}K"
    return str(n)


def plot_results(results, sizes, title, filename, subtitle=""):
    """
    results : dict  {algo_name: {"means": [...], "stds": [...], "sizes_done": [...]}}
    """
    _apply_style()
    fig, ax = plt.subplots(figsize=(11, 6.5))
    fig.patch.set_facecolor(STYLE["figure.facecolor"])

    for idx, (name, data) in enumerate(results.items()):
        colour = COLOURS[idx % len(COLOURS)]
        xs   = data["sizes_done"]
        ys   = data["means"]
        errs = data["stds"]

        ax.plot(xs, ys, marker="o", markersize=5, linewidth=2.2,
                color=colour, label=name, zorder=3)
        ax.fill_between(xs,
                        [max(0, m - s) for m, s in zip(ys, errs)],
                        [m + s for m, s in zip(ys, errs)],
                        alpha=0.18, color=colour)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: _human_size(int(x))))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(
        lambda y, _: f"{y*1000:.1f} ms" if y < 1 else f"{y:.2f} s"))

    ax.set_xlabel("Array Size  (log scale)", fontsize=12, labelpad=8)
    ax.set_ylabel("Time  (log scale)", fontsize=12, labelpad=8)
    ax.set_title(title, fontsize=15, fontweight="bold", pad=14)
    if subtitle:
        ax.text(0.5, 1.01, subtitle, transform=ax.transAxes,
                ha="center", fontsize=9, color="#8b949e")
    ax.grid(True, which="both", linestyle="--", alpha=0.4)
    ax.legend(loc="upper left", fontsize=11, framealpha=0.8)

    fig.tight_layout()
    fig.savefig(filename, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  [OK] Saved: {filename}")


def plot_noise_comparison(noise_results, title, filename):
    """
    noise_results : dict
        { algo_name : { noise_label : {"sizes_done": [...], "means": [...], "stds": [...]} } }
    """
    _apply_style()
    n_algos = len(noise_results)
    fig, axes = plt.subplots(1, n_algos, figsize=(6 * n_algos, 6),
                             sharey=False)
    if n_algos == 1:
        axes = [axes]
    fig.patch.set_facecolor(STYLE["figure.facecolor"])

    noise_styles = {
        "0% (sorted)":    ("#58a6ff", "o", "solid"),
        "5% noise":       ("#3fb950", "s", "dashed"),
        "50% noise":      ("#f78166", "^", "dotted"),
    }

    for ax, (algo_name, noise_data) in zip(axes, noise_results.items()):
        for noise_label, data in noise_data.items():
            colour, marker, ls = noise_styles.get(
                noise_label, ("#c9d1d9", "x", "solid"))
            xs   = data["sizes_done"]
            ys   = data["means"]
            errs = data["stds"]
            ax.plot(xs, ys, marker=marker, markersize=5, linewidth=2,
                    color=colour, linestyle=ls, label=noise_label, zorder=3)
            ax.fill_between(xs,
                            [max(0, m - s) for m, s in zip(ys, errs)],
                            [m + s for m, s in zip(ys, errs)],
                            alpha=0.15, color=colour)

        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.xaxis.set_major_formatter(
            ticker.FuncFormatter(lambda x, _: _human_size(int(x))))
        ax.yaxis.set_major_formatter(
            ticker.FuncFormatter(
                lambda y, _: f"{y*1000:.1f} ms" if y < 1 else f"{y:.2f} s"))
        ax.set_title(algo_name, fontsize=12, fontweight="bold", pad=8)
        ax.set_xlabel("Array Size (log scale)", fontsize=10)
        ax.set_ylabel("Time (log scale)", fontsize=10)
        ax.grid(True, which="both", linestyle="--", alpha=0.4)
        ax.legend(loc="upper left", fontsize=9, framealpha=0.8)

    fig.suptitle(title, fontsize=14, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(filename, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  [OK] Saved: {filename}")

# ---------------------------------------------------------------------------
# ─── EXPERIMENT RUNNERS ────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def run_experiment_A(algo_ids, sizes, repetitions):
    """
    Part B – Random arrays experiment → result1.png
    Returns results dict ready for plot_results().
    """
    print("\n═══ Part B: Random Arrays Experiment ═══")
    results = {}
    for aid in algo_ids:
        name, fn = ALGORITHM_MAP[aid]
        print(f"\n  [{name}]")
        means, stds, sizes_done = [], [], []
        skip = False
        for sz in sizes:
            if skip:
                print(f"    size={_human_size(sz):>6}  -> skipped (too slow)")
                continue
            mean, std = run_timing(fn, sz, repetitions, random_array)
            print(f"    size={_human_size(sz):>6}  mean={mean:.4f}s  std={std:.4f}s")
            means.append(mean); stds.append(std); sizes_done.append(sz)
            if mean > SKIP_THRESHOLD_SECONDS:
                print(f"    [!] Skipping larger sizes for {name} "
                      f"(avg > {SKIP_THRESHOLD_SECONDS}s)")
                skip = True
        results[name] = {"means": means, "stds": stds, "sizes_done": sizes_done}
    return results


def run_experiment_B(algo_ids, sizes, repetitions, noise_fractions):
    """
    Part C – Nearly-sorted arrays experiment → result2.png
    Returns noise_results dict ready for plot_noise_comparison().
    noise_fractions is a list of floats, e.g. [0.05, 0.20]
    """
    print("\n═══ Part C: Nearly-Sorted Arrays Experiment ═══")
    noise_results = {}       # {algo: {label: {sizes_done, means, stds}}}

    noise_labels = {0.0: "0% (sorted)", 0.05: "5% noise", 0.50: "50% noise"}
    fractions = [0.0] + list(noise_fractions)   # always include fully sorted

    for aid in algo_ids:
        name, fn = ALGORITHM_MAP[aid]
        print(f"\n  [{name}]")
        noise_results[name] = {}

        for frac in fractions:
            label = noise_labels.get(frac, f"{int(frac*100)}% noise")
            print(f"    noise={label}")
            means, stds, sizes_done = [], [], []
            skip = False
            for sz in sizes:
                if skip:
                    print(f"      size={_human_size(sz):>6}  -> skipped")
                    continue
                gen_kwargs = {"noise_fraction": frac} if frac > 0 else {}
                arr_gen = nearly_sorted_array if frac >= 0 else random_array
                if frac == 0.0:
                    # perfectly sorted array
                    arr_gen = lambda s, **kw: list(range(s))
                    gen_kwargs = {}
                mean, std = run_timing(fn, sz, repetitions, arr_gen, **gen_kwargs)
                print(f"      size={_human_size(sz):>6}  mean={mean:.4f}s  std={std:.4f}s")
                means.append(mean); stds.append(std); sizes_done.append(sz)
                if mean > SKIP_THRESHOLD_SECONDS:
                    skip = True
            noise_results[name][label] = {
                "sizes_done": sizes_done, "means": means, "stds": stds
            }
    return noise_results

# ---------------------------------------------------------------------------
# ─── CLI ───────────────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        prog="run_experiments.py",
        description="Sorting Algorithm Comparison – Data Structures Spring 2026",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Algorithm IDs:
  1 – Bubble Sort
  2 – Selection Sort
  3 – Insertion Sort
  4 – Merge Sort
  5 – Quick Sort

Experiment types (-e):
  1 – Nearly sorted with 5%  noise
  2 – Nearly sorted with 50% noise
  (you can pass both: -e 1 2)

Examples:
  python run_experiments.py
  python run_experiments.py -a 1 2 5 -s 100 500 3000 -e 1 -r 20
  python run_experiments.py -a 3 4 5 -s 100 1000 10000 100000 -e 1 2 -r 5
""",
    )
    parser.add_argument(
        "-a", "--algorithms", nargs="+", type=int, default=[1, 4, 5],
        metavar="ID",
        help="Algorithm IDs to compare (default: 1 4 5)",
    )
    parser.add_argument(
        "-s", "--sizes", nargs="+", type=int,
        default=[100, 500, 1_000, 5_000, 10_000, 50_000, 100_000, 500_000, 1_000_000],
        metavar="N",
        help="Array sizes to test (default: 100 500 1K 5K 10K 50K 100K 500K 1M)",
    )
    parser.add_argument(
        "-e", "--experiment", nargs="+", type=int, choices=[1, 2], default=[1, 2],
        metavar="TYPE",
        help="Experiment types for Part C: 1=5%% noise  2=50%% noise (default: 1 2)",
    )
    parser.add_argument(
        "-r", "--repetitions", type=int, default=5,
        metavar="R",
        help="Repetitions per (algorithm, size) pair (default: 5)",
    )
    parser.add_argument(
        "--out-dir", default=".",
        metavar="DIR",
        help="Output directory for PNG files (default: current directory)",
    )
    return parser


# ---------------------------------------------------------------------------
# ─── MAIN ──────────────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

def main():
    parser = build_parser()
    args = parser.parse_args()

    # ── validate algorithm IDs
    for aid in args.algorithms:
        if aid not in ALGORITHM_MAP:
            parser.error(f"Unknown algorithm ID: {aid}. Valid IDs are 1–5.")
    if len(args.algorithms) < 2:
        parser.error("Please select at least 2 algorithms to compare.")

    sizes      = sorted(set(args.sizes))
    algo_ids   = sorted(set(args.algorithms))
    reps       = args.repetitions
    out_dir    = args.out_dir

    os.makedirs(out_dir, exist_ok=True)

    algo_names = [ALGORITHM_MAP[a][0] for a in algo_ids]
    print("=" * 60)
    print("  Sorting Algorithm Comparison  |  Data Structures S2026")
    print("=" * 60)
    print(f"  Algorithms  : {', '.join(algo_names)}")
    print(f"  Sizes       : {[_human_size(s) for s in sizes]}")
    print(f"  Repetitions : {reps}")
    print(f"  Exp. types  : {args.experiment}")
    print("=" * 60)

    # ── Part B – random arrays → result1.png
    results_A = run_experiment_A(algo_ids, sizes, reps)
    path1 = os.path.join(out_dir, "result1.png")
    plot_results(
        results_A, sizes,
        title="Sorting Algorithm Comparison – Random Arrays",
        subtitle=f"repetitions={reps} | sizes up to {_human_size(sizes[-1])}",
        filename=path1,
    )

    # ── Part C – nearly sorted → result2.png
    noise_map = {1: 0.05, 2: 0.50}
    noise_fractions = [noise_map[e] for e in args.experiment]
    results_B = run_experiment_B(algo_ids, sizes, reps, noise_fractions)
    path2 = os.path.join(out_dir, "result2.png")
    plot_noise_comparison(
        results_B,
        title="Sorting Algorithm Comparison – Nearly-Sorted Arrays",
        filename=path2,
    )

    print("\n  All done!")
    print(f"  result1.png -> {os.path.abspath(path1)}")
    print(f"  result2.png -> {os.path.abspath(path2)}")


if __name__ == "__main__":
    # Increase recursion limit for large Quick/Merge sort on edge cases
    sys.setrecursionlimit(100_000)
    main()
