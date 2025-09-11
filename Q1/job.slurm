#!/bin/bash
#SBATCH --job-name=mpi_experiment
#SBATCH --output=job_output.log
#SBATCH --error=job_error.log
#SBATCH --ntasks=1
#SBATCH --nodes=1
#SBATCH --time=00:10:00

# Step 1: Prepare the environment.
echo "Loading OpenMPI module..."
module load openmpi

# Step 2: Run the program.
echo "Running MPI program with $SLURM_NTASKS cores..."
mpirun -np $SLURM_NTASKS ./sparse_mm < large_input.txt
