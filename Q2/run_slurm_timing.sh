#!/usr/bin/env bash
# This script uses a Slurm Job Array to measure the performance of the MPI
# triangle counting program for various process counts on a single node.
# This version captures the execution time printed by the Python script itself.

# --- SBATCH Directives ---
#SBATCH --job-name=TrianglePerfTest
#SBATCH --output=perf_test_%A_%a.out  # Unique log for each array task
#SBATCH --error=perf_test_%A_%a.err   # Unique error log for each array task

# --- Resource Allocation ---
# We request a single node for this "strong scaling" test.
#SBATCH --nodes=1
# Request the maximum number of tasks we will test with. This ensures
# the allocated node has enough cores for all runs in the array.
#SBATCH --ntasks=24
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=2G
#SBATCH --time=01:00:00  # Allocate enough time for all tests to run

# --- Job Array Configuration ---
# This will create 24 jobs, with SLURM_ARRAY_TASK_ID ranging from 1 to 24.
#SBATCH --array=1-24

# ==============================================================================
# --- Strict Mode & Configuration ---
# ==============================================================================
set -euo pipefail

# The Python script to execute.
APP="python3 mpi_mapreduce.py" # The script name was changed in the original prompt
# The output file for the aggregated timing data.
OUT_CSV="performance_results_10000.csv"

# ==============================================================================
# ACTION REQUIRED: CONFIGURE YOUR CLUSTER ENVIRONMENT
# You MUST uncomment and edit the 'module load' line below for the job to work.
# ==============================================================================
echo "Loading environment modules..."
# module load python/3.12.5 openmpi/4.1.5  # <-- UNCOMMENT AND EDIT THIS LINE

# --- SCRIPT EXECUTION ---

# The number of processes for this specific job in the array.
NUM_PROCESSES=$SLURM_ARRAY_TASK_ID

# --- Create the CSV header (only for the first task in the array) ---
# This prevents a race condition where multiple jobs try to create the file.
if [ "$SLURM_ARRAY_TASK_ID" -eq 1 ]; then
    echo "Processes,ExecutionTime" > "$OUT_CSV"
    echo "================================================="
    echo "Starting Slurm performance test for 1 to 24 processes..."
    echo "Results will be saved in $OUT_CSV"
    echo "================================================="
fi

echo "==> Running test with np=$NUM_PROCESSES"

# --- Execute and Capture Output from the MPI Application ---
# We run the mpirun command and capture its standard output into a variable.
# The standard error is redirected to the Slurm error file (2>&1 can be used to merge).
RUN_OUTPUT=$(mpirun --oversubscribe -np "$NUM_PROCESSES" $APP "$1")

# --- Parse the time from the script's output and append to the CSV ---
# We find the line containing "Total execution time", and use awk to grab the
# 4th field, which is the time value.
EXEC_TIME=$(echo "$RUN_OUTPUT" | grep "Total execution time" | awk '{print $4}')

# Append the result for this task to the main CSV file.
# We use a lock to prevent multiple array jobs from writing to the CSV at the same time.
flock -x "$OUT_CSV" -c "echo '$NUM_PROCESSES,$EXEC_TIME' >> '$OUT_CSV'"

echo "==> Finished test with np=$NUM_PROCESSES. Time: $EXEC_TIME seconds."

# --- Final message (only for the last task in the array) ---
if [ "$SLURM_ARRAY_TASK_ID" -eq 24 ]; then
    # Give a brief moment for any lingering file writes to finish
    sleep 5
    # Sort the final CSV file by the number of processes
    sort -t, -n -o "$OUT_CSV" "$OUT_CSV"
    echo "================================================="
    echo "All performance tests finished!"
    echo "Final results sorted and saved to $OUT_CSV"
    echo "You can now run 'python3 plot_results.py' to generate graphs."
fi
