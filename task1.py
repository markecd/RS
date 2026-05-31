#!/usr/bin/env python3

import os
import subprocess
import shutil
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--dry-run", action="store_true",
                    help="Skip simulation, just parse existing stats files")
args = parser.parse_args()

GEM5_BIN  = os.environ.get("GEM5_BIN", "gem5")
GEM5_ROOT = os.environ.get("GEM5_ROOT")

COMPUTE_UNITS = [2, 4, 8]
KERNELS = ["naive", "opt"]



def run_gem5(cu, kernel):
    """Run one GEM5 simulation and save stats to a local file."""
    stats_file = f"stats_task1_{kernel}_cu{cu}.txt"
    if args.dry_run:
        return stats_file

    binary = f"histogram/bin/histogram_{kernel}.bin"
    subprocess.run([
        GEM5_BIN,
        f"{GEM5_ROOT}/configs/example/apu_se.py",
        "-n", "3",
        "--num-compute-units", str(cu),
        "--gfx-version=gfx902",
        "-c", binary,
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    shutil.copy("m5out/stats.txt", stats_file)
    return stats_file


def parse_stats(stats_file, cu):
    """Extract the first occurrence of each metric from the stats file."""
    with open(stats_file) as f:
        lines = f.readlines()

    # keep only first stats block
    end = next(i for i, l in enumerate(lines)
               if l.startswith("---------- End Simulation Statistics"))
    lines = lines[:end]

    def first(prefix):
        for line in lines:
            if line.startswith(prefix):
                return line.split()[1]
        return None

    load_latency = float(first("system.cpu3.loadLatencyDist::mean"))

    v_alu, lds, cycles, vpc_sum = 0, 0, 0, 0.0
    for i in range(cu):
        v_alu    += int  (first(f"system.cpu3.CUs{i}.vALUInsts"))
        lds      += int  (first(f"system.cpu3.CUs{i}.ldsBankAccesses"))
        cycles   += int  (first(f"system.cpu3.CUs{i}.totalCycles"))
        vpc_sum  += float(first(f"system.cpu3.CUs{i}.vpc"))

    return {
        "load_latency": load_latency,
        "vALUInsts":    v_alu    // cu,   # average per CU
        "ldsBankAccess": lds     // cu,
        "totalCycles":  cycles   // cu,
        "vpc":          vpc_sum  /  cu,
    }



results = {}
for cu in COMPUTE_UNITS:
    for kernel in KERNELS:
        stats_file = run_gem5(cu, kernel)
        results[(cu, kernel)] = parse_stats(stats_file, cu)

print("| CU | Kernel  | Load Latency | vALUInsts | ldsBankAccess | Total Cycles | VPC   |")
print("|----|---------|--------------|-----------|---------------|--------------|-------|")
for cu in COMPUTE_UNITS:
    for kernel in KERNELS:
        m = results[(cu, kernel)]
        print(f"| {cu:2} | {kernel:7} | {m['load_latency']:12.2f} | "
              f"{m['vALUInsts']:9} | {m['ldsBankAccess']:13} | "
              f"{m['totalCycles']:12} | {m['vpc']:.3f} |")
        
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 3, figsize=(15, 8))
fig.suptitle("Histogram kernel performance: Naive vs Optimized")

metrics = ["load_latency", "vALUInsts", "ldsBankAccess", "totalCycles", "vpc"]
titles  = ["Load Latency", "vALU Insts", "LDS Bank Access", "Total Cycles", "VPC"]

for ax, metric, title in zip(axes.flat, metrics, titles):
    naive = [results[(cu, "naive")][metric] for cu in COMPUTE_UNITS]
    opt   = [results[(cu, "opt")]  [metric] for cu in COMPUTE_UNITS]
    ax.plot(COMPUTE_UNITS, naive, marker='o', label="Naive")
    ax.plot(COMPUTE_UNITS, opt,   marker='o', label="Opt")
    ax.set_title(title)
    ax.set_xlabel("Compute Units")
    ax.set_xticks(COMPUTE_UNITS)
    ax.legend()

axes.flat[-1].set_visible(False) 
plt.tight_layout()
plt.savefig("task1_graphs.png", dpi=150)
print("Graf shranjen: task1_graphs.png")