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
KERNELS = ["divergent", "uniform"]



def run_gem5(cu):
    """Run one GEM5 simulation and save stats to a local file."""
    stats_file = f"stats_task3_cu{cu}.txt"
    if args.dry_run:
        return stats_file

    subprocess.run([
        GEM5_BIN,
        f"{GEM5_ROOT}/configs/example/apu_se.py",
        "-n", "3",
        "--num-compute-units", str(cu),
        "--gfx-version=gfx902",
        "-c", "spmv/bin/spmv.bin",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    shutil.copy("m5out/stats.txt", stats_file)
    return stats_file


def parse_stats(stats_file, cu, block=0):
    """Extract the first occurrence of each metric from the stats file."""
    with open(stats_file) as f:
        lines = f.readlines()

    blocks = []
    current = []

    for line in lines:
        if line.startswith("---------- End Simulation Statistics"):
            blocks.append(current)
            current = []
        else:
            current.append(line)

    block_lines = blocks[block]

    def first(prefix):
        for line in block_lines:
            if line.startswith(prefix):
                return line.split()[1]
        return None

    v_alu = 0
    cf_div_mean = 0.0
    cf_div_stdev = 0.0
    global_reads = 0
    global_writes = 0
    coalesced = 0

    for i in range(cu):
        v_alu    += int  (first(f"system.cpu3.CUs{i}.vALUInsts"))
        cf_div_mean      += float(first(f"system.cpu3.CUs{i}.controlFlowDivergenceDist::mean"))
        cf_div_stdev   += float(first(f"system.cpu3.CUs{i}.controlFlowDivergenceDist::stdev"))
        global_reads  += int(first(f"system.cpu3.CUs{i}.globalReads"))
        global_writes  += int(first(f"system.cpu3.CUs{i}.globalWrites"))
        coalesced  += int(first(f"system.cpu3.CUs{i}.coalsrLineAddresses::total"))

    return {
        "cf_div_mean":  cf_div_mean  / cu,
        "cf_div_stdev": cf_div_stdev / cu,
        "vALUInsts":    v_alu        // cu,
        "globalReads":  global_reads // cu,
        "globalWrites": global_writes// cu,
        "coalesced":    coalesced    // cu,
    }



results = {}
for cu in COMPUTE_UNITS:
    stats_file = run_gem5(cu)
    results[(cu, "divergent")] = parse_stats(stats_file, cu, block=0)
    results[(cu, "uniform")] = parse_stats(stats_file, cu, block=1)


print("| CU | Kernel    | CF div mean | CF div stdev | vALUInsts | globalReads | globalWrites | coalesced |")
print("|----|-----------|-------------|--------------|-----------|-------------|--------------|-----------|")
for cu in COMPUTE_UNITS:
    for kernel in KERNELS:
        m = results[(cu, kernel)]
        print(f"| {cu:2} | {kernel:9} | {m['cf_div_mean']:11.4f} | "
              f"{m['cf_div_stdev']:12.4f} | {m['vALUInsts']:9} | "
              f"{m['globalReads']:11} | {m['globalWrites']:12} | {m['coalesced']:9} |")
 
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
 
fig, axes = plt.subplots(2, 3, figsize=(15, 8))
fig.suptitle("SpMV kernel performance: Divergent vs Uniform")
 
metrics = ["cf_div_mean", "cf_div_stdev", "vALUInsts", "globalReads", "coalesced"]
titles  = ["CF Divergence Mean", "CF Divergence Stdev", "vALU Insts", "Global Reads", "Coalesced Accesses"]
 
for ax, metric, title in zip(axes.flat, metrics, titles):
    div  = [results[(cu, "divergent")][metric] for cu in COMPUTE_UNITS]
    unif = [results[(cu, "uniform")]  [metric] for cu in COMPUTE_UNITS]
    ax.plot(COMPUTE_UNITS, div,  marker='o', label="Divergent")
    ax.plot(COMPUTE_UNITS, unif, marker='o', label="Uniform")
    ax.set_title(title)
    ax.set_xlabel("Compute Units")
    ax.set_xticks(COMPUTE_UNITS)
    ax.legend()
 
axes.flat[-1].set_visible(False)
plt.tight_layout()
plt.savefig("task3_graphs.png", dpi=150)
print("Graf shranjen: task3_graphs.png")