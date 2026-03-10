#!/bin/bash
#SBATCH --job-name=goedel_f2f_amend
#SBATCH --qos=normal
#SBATCH --gres=gpu:2
#SBATCH --cpus-per-task=8
#SBATCH --mem=400G
#SBATCH --time=24:00:00
#SBATCH --output=/gpfs/projects/mathai/lean-bench/slurmouts/slurm-goedel_f2f_amend.out

module load gcc cuda
cd /gpfs/projects/mathai/lean-bench/
apptainer exec   --cleanenv   --bind /gpfs/scrubbed/lean-bench:/work   --bind /gpfs/scrubbed/lean-bench/home:/home/$USER   --bind /gpfs/scrubbed/lean-bench/tmp:/tmp   --bind /gpfs/projects/mathai/lean-bench/LLMsLean:/app   --pwd /app  --nv lean-env.sif /bin/bash -c "ls; cd ./winter; python3 run.py --final goedel True F 1 4"
exit