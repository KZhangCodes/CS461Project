import statistics
import numpy as np
import matplotlib.pyplot as plt
from city_agent import CityAgent
from city_graph import CityGraph

ALGORITHMS = ["bfs", "dfs", "iddfs", "best_first", "astar"]
REPEAT = 5

#single search with animation and returns metrics
def _run_once(graph: CityGraph, algorithm: str, start: str, goal: str) -> dict | None:
    agent = CityAgent(graph, start, goal)
    branch_counts: list[int] = []
    peak_frontier = 0
    visited: set[str] = set()

    for event in getattr(agent, algorithm)():
        if event[0] == "step":
            current, frontier = event[1], event[2]
            visited.add(current)
            branch_counts.append(len(graph.neighbors(current)))
            peak_frontier = max(peak_frontier, len(frontier))
        elif event[0] == "done":
            path, nodes_expanded, elapsed_ms, peak_kb, heuristic_stats, nodes_generated = event[1:]
            if path is None:
                return None
            return {"path_length": len(path) - 1, "path_cost": heuristic_stats.get("total_cost") if heuristic_stats else None, "nodes_expanded": nodes_expanded,
                "nodes_generated": nodes_generated, "branch_avg": statistics.mean(branch_counts) if branch_counts else 0.0, "branch_max": max(branch_counts) if branch_counts else 0,
                "peak_frontier": peak_frontier, "peak_footprint": peak_frontier + len(visited), "elapsed_ms": elapsed_ms, "peak_kb": peak_kb,}
    return None

#compute mean and std for each metric, path_cost/path_length copied from first run
def _summarize(runs: list[dict]) -> dict:
    numeric_keys = ["elapsed_ms", "peak_kb", "nodes_expanded", "nodes_generated", "branch_avg", "branch_max", "peak_frontier", "peak_footprint"]
    summary = {}
    for metric in numeric_keys:
        metric_values = [run[metric] for run in runs]
        summary[f"{metric}_mean"] = statistics.mean(metric_values)
        summary[f"{metric}_std"] = statistics.stdev(metric_values) if len(metric_values) > 1 else 0.0
    summary["path_cost"] = runs[0]["path_cost"]
    summary["path_length"] = runs[0]["path_length"]
    return summary

#run each algorithm multiple times, marks which match astar path length
def run_benchmark(graph: CityGraph, start: str, goal: str, algorithms: list[str], repeats: int = REPEAT) -> dict[str, dict | None]:
    results = {}
    for algorithm in algorithms:
        completed_runs = [run for _ in range(repeats) if (run := _run_once(graph, algorithm, start, goal)) is not None] #remove runs wih no path
        if not completed_runs:
            results[algorithm] = None
            continue
        results[algorithm] = _summarize(completed_runs)

    #find shortest path length for algorithms that found a path
    successful_results = [s for s in results.values() if s is not None]
    if successful_results:
        min_path_length = min(s["path_length"] for s in successful_results)
        for algorithm_summary in results.values():
            if algorithm_summary is not None:
                algorithm_summary["matches_optimal"] = algorithm_summary["path_length"] == min_path_length
    return results

#runs the benchmark and displays results with table/charts
def show_benchmark_window(graph: CityGraph, start: str, goal: str, algorithms: list[str], repeats: int = REPEAT) -> None:
    benchmark_results = run_benchmark(graph, start, goal, algorithms, repeats)
    valid_results = {algorithm: summary for algorithm, summary in benchmark_results.items() if summary is not None}

    if not valid_results:
        fig, ax = plt.subplots(figsize=(4, 2))
        ax.axis("off")
        ax.text(0.5, 0.5, "No paths found for any algorithm.", ha="center", va="center")
        fig.show()
        return

    fig = plt.figure(figsize=(16, 10))
    fig.canvas.manager.set_window_title(f"Benchmark: {start} → {goal}  ({repeats} runs each)")
    _draw_table(fig.add_axes([0.02, 0.48, 0.96, 0.46]), valid_results, repeats)
    _draw_bar_chart(fig.add_axes([0.06, 0.06, 0.26, 0.34]), valid_results, "elapsed_ms", "ms", "Time (mean std)", "steelblue")
    _draw_bar_chart(fig.add_axes([0.38, 0.06, 0.26, 0.34]), valid_results, "peak_kb", "KB", "Peak memory (mean std)", "darkorange")
    _draw_nodes_chart(fig.add_axes([0.70, 0.06, 0.26, 0.34]), valid_results)
    fig.show()

#draw benchmark table with all metrics for each selected algorithm
def _draw_table(ax, results: dict, repeats: int) -> None:
    ax.axis("off")
    col_labels = ["Algorithm", "Time mean std (ms)", "Mem mean std (KB)", "Expanded", "Generated", "Branch avg", "Branch max", "Peak frontier", "Peak footprint", "Path length", "Path cost", "Optimal?"]
    rows = []
    for algorithm, summary in results.items():
        cost_str = f"{summary['path_cost']:.2f}" if summary["path_cost"] is not None else "N/A"
        optimal_str = "yes" if summary.get("matches_optimal") else "no"
        rows.append([algorithm.upper(), f"{summary['elapsed_ms_mean']:.3f} {summary['elapsed_ms_std']:.3f}", f"{summary['peak_kb_mean']:.0f} {summary['peak_kb_std']:.0f}",
            f"{summary['nodes_expanded_mean']:.1f}", f"{summary['nodes_generated_mean']:.1f}", f"{summary['branch_avg_mean']:.2f}", f"{summary['branch_max_mean']:.1f}",
            f"{summary['peak_frontier_mean']:.1f}", f"{summary['peak_footprint_mean']:.1f}", str(summary["path_length"]), cost_str, optimal_str,])
    table = ax.table(cellText=rows, colLabels=col_labels, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(8.5)
    table.scale(1, 1.8)
    ax.set_title(f"Benchmark summary  ({repeats} runs per algorithm)", fontsize=10, pad=14)

def _draw_bar_chart(ax, results: dict, metric_key: str, ylabel: str, title: str, color: str) -> None:
    algorithm_names = list(results.keys())
    means = [results[algorithm][f"{metric_key}_mean"] for algorithm in algorithm_names]
    stds = [results[algorithm][f"{metric_key}_std"]  for algorithm in algorithm_names]
    ax.bar(range(len(algorithm_names)), means, yerr=stds, capsize=4, color=color, alpha=0.85)
    ax.set_xticks(range(len(algorithm_names)))
    ax.set_xticklabels([algorithm.upper() for algorithm in algorithm_names], fontsize=7)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=9)

#draw grouped bar chart comparing nodes expanded vs nodes generated
def _draw_nodes_chart(ax, results: dict) -> None:
    algorithm_names = list(results.keys())
    expanded_means = [results[algorithm]["nodes_expanded_mean"]  for algorithm in algorithm_names]
    generated_means = [results[algorithm]["nodes_generated_mean"] for algorithm in algorithm_names]
    x = np.arange(len(algorithm_names))
    width = 0.35
    ax.bar(x - width / 2, expanded_means,  width, label="Expanded",  color="mediumseagreen", alpha=0.85)
    ax.bar(x + width / 2, generated_means, width, label="Generated", color="mediumpurple",   alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels([algorithm.upper() for algorithm in algorithm_names], fontsize=7)
    ax.set_title("Nodes", fontsize=9)
    ax.legend(fontsize=7)