#!/bin/bash

#SBATCH --job-name=ead-html-validator
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --time=05-00:00:00
#SBATCH --mem=8GB
#SBATCH --mail-type=ALL
#SBATCH --mail-user=rasan@nyu.edu
#SBATCH --output=validator-%j.log

. /etc/profile

set -u

APP_NAME=ead-html-validator

APP_HOME=$HOME/work/$APP_NAME

module load python/intel/3.8.6

source $HOME/venv/$APP_NAME/bin/activate

echo "Date              = $(date)"
echo "Hostname          = $(hostname -s)"
echo "Working Directory = $(pwd)"
echo ""
echo "Number of Nodes Allocated      = $SLURM_JOB_NUM_NODES"
echo "Number of Tasks Allocated      = $SLURM_NTASKS"
echo "Number of Cores/Task Allocated = $SLURM_CPUS_PER_TASK"

$APP_HOME/runtimes.sh
