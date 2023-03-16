#!/bin/bash

#SBATCH --job-name=ead-html-validator
#SBATCH --nodes=1
#SBATCH --tasks-per-node=1
#SBATCH --cpus-per-task=8
#SBATCH --time=05-00:00:00
#SBATCH --mem=8GB
#SBATCH --mail-type=ALL
#SBATCH --mail-user=rasan@nyu.edu
#SBATCH --output=slurm-%j.out

set -u

. /etc/profile

APP_NAME=ead-html-validaor

APP_HOME=$HOME/work/$NAME

export PATH=$HOME/bin:$PATH

module load module load python/intel/3.8.6

source $HOME/venv/$APP_NAME/bin/activate

# set -x

srun \
	--job-name=${APP_NAME} \
	--nodes=1 \
	--ntasks=1 \
	--cpus-per-task=$SLURM_CPUS_PER_TASK \
	--exclusive \
	$APP_HOME/runtimes.sh &

