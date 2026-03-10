#!/bin/bash
#SBATCH --job-name=deepseek_ctx_amend
#SBATCH --qos=normal
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=200G
#SBATCH --time=12:00:00
#SBATCH --output=/gpfs/projects/mathai/lean-bench/slurmouts/slurm-deepseek_ctx_amend.out

module load gcc cuda
cd /gpfs/projects/mathai/lean-bench/
apptainer exec   --cleanenv   --bind /gpfs/scrubbed/lean-bench:/work   --bind /gpfs/scrubbed/lean-bench/home:/home/$USER   --bind /gpfs/scrubbed/lean-bench/tmp:/tmp   --bind /gpfs/projects/mathai/lean-bench/LLMsLean:/app   --pwd /app  --nv lean-env.sif /bin/bash -c "ls; cd ./winter; python3 run.py --final deepseek True C 1 4"
exit