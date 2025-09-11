#!/bin/bash
2 #SBATCH --job-name=TriangleCount-MultiNode
3 #SBATCH --output=multinode_%j.out
4 #SBATCH --error=multinode_%j.err
5 #SBATCH --nodes=2
6 #SBATCH --ntasks-per-node=4
7 #SBATCH --cpus-per-task=1
8 #SBATCH --time=00:30:00
9
10 # Load necessary modules
11 module load python/3.12.5 openmpi/4.1.5
12
13 # Set process count and run the job
14 NPROCS=8 # Must match nodes * ntasks-per-node
15 mpirun --oversubscribe -np $NPROCS python3 mpi_mapreduce.py "$1"