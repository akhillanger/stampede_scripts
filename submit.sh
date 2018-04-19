#!/usr/bin/bash

#Run command - ./submit.sh <number_of_nodes> <time> <collective>
sbatch -N $1 --ntasks-per-node 1 -t $2 -p skx-normal run.py $1 $3
