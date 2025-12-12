import pandas as pd
import matplotlib.pyplot as plt
import sys
import os

# --- CONFIGURATION ---
RESULTS_FILE = "results/benchmark_data.csv"  # Path to your CSV
OUTPUT_DIR = "results"                       # Where to save images


def plot_benchmark():
    if not os.path.exists(RESULTS_FILE):
        print(
            f"Error: Could not find {RESULTS_FILE}. Run the benchmark first.")
        sys.exit(1)

    # Load data
    df = pd.read_csv(RESULTS_FILE)

    # --- PLOT 1: Execution Time (Log Scale often better for SAT) ---
    plt.figure(figsize=(12, 6))

    pivot_time = df.pivot(index='problem', columns='solver', values='time_sec')

    ax1 = pivot_time.plot(kind='bar', width=0.8, figsize=(12, 6), rot=45)

    plt.title('Solver Execution Time Comparison')
    plt.ylabel('Time (seconds)')
    plt.xlabel('Problem Instance')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(title='Solver')
    plt.tight_layout()

    time_plot_path = os.path.join(OUTPUT_DIR, 'benchmark_time.png')
    plt.savefig(time_plot_path)
    print(f"Saved time plot to {time_plot_path}")

    # --- PLOT 2: Peak Memory Usage ---
    plt.figure(figsize=(12, 6))

    pivot_mem = df.pivot(index='problem', columns='solver', values='memory_kb')

    pivot_mem = pivot_mem / 1024

    ax2 = pivot_mem.plot(kind='bar', width=0.8, figsize=(
        12, 6), rot=45, color=['#ff9999', '#66b3ff', '#99ff99'])

    plt.title('Solver Peak Memory Usage')
    plt.ylabel('Memory (MB)')
    plt.xlabel('Problem Instance')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(title='Solver')
    plt.tight_layout()

    # Save
    mem_plot_path = os.path.join(OUTPUT_DIR, 'benchmark_memory.png')
    plt.savefig(mem_plot_path)
    print(f"Saved memory plot to {mem_plot_path}")


if __name__ == "__main__":
    plot_benchmark()
