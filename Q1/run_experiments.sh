#!/bin/bash

# --- Configuration ---
MAX_CORES=24
CORE_COUNTS=({1..24})
export INPUT_FILE="large_input.txt"
export OUTPUT_DATA_FILE="results_full_fast.csv"

# --- Setup ---
echo "This script will request a SINGLE allocation for $MAX_CORES cores and then"
echo "run a worker script inside it to perform all 24 experiments."
echo "------------------------------------------------------------------"

module load openmpi
echo "Compiling the C++ code..."
mpic++ -std=c++11 -o sparse_mm sparse_mm.cpp

# Make the new worker script executable
chmod +x run_loop_inside_salloc.sh

# Create a clean header for our CSV file.
echo "Cores,Time" > $OUTPUT_DATA_FILE

# --- Export variables to the sub-shell ---
# The 'export' command makes these variables available to child processes,
# which is exactly what our salloc worker script is.
# We convert the array to a simple string for easy transport.
export CORE_COUNTS_STR="${CORE_COUNTS[*]}"

# --- The Single Allocation Block ---
echo "Requesting a single allocation for up to $MAX_CORES cores. This may take a moment..."

# This is much simpler now. salloc just runs our new script.
salloc --ntasks=$MAX_CORES ./run_loop_inside_salloc.sh

echo "-------------------------------------------"
echo "Fast experiments finished. Final data saved to $OUTPUT_DATA_FILE:"
cat $OUTPUT_DATA_FILE
