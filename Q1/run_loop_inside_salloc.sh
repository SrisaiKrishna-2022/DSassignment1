#!/bin/bash

echo "--- Worker script started on a compute node. ---"
module load openmpi
read -r -a core_array <<< "$CORE_COUNTS_STR"
for cores in "${core_array[@]}"; do
    echo "--> Running experiment with $cores cores..."
    mpirun --mca pml ob1 --mca btl tcp,self,vader -np $cores ./sparse_mm < "$INPUT_FILE" 2> temp_error_log.txt
    TIME_OUTPUT=$(grep 'TIME_TAKEN' temp_error_log.txt)
    if [ -n "$TIME_OUTPUT" ]; then
        CORES_USED=$(echo "$TIME_OUTPUT" | cut -d',' -f2)
        TIME_TAKEN=$(echo "$TIME_OUTPUT" | cut -d',' -f3)
        echo "$CORES_USED,$TIME_TAKEN" >> "$OUTPUT_DATA_FILE"
    else
        echo "Error running with $cores cores."
    fi
done

echo "--- Worker script finished. ---"
rm -f temp_error_log.txt
