#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset
# set -o xtrace

# Set magic variables for current file & dir
__dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
__file="${__dir}/$(basename "${BASH_SOURCE[0]}")"
__base="$(basename ${__file} .sh)"
__root="$(cd "$(dirname "${__dir}")" && pwd)" # <-- change this as it depends on your app

export GYM_NEYBOY_GAME_URL='http://localhost:8000'
#export GYM_NEYBOY_BROWSER_WS_ENDPOINT=ws://localhost:3000

OUT="${1:-/mnt/hdd/neyboy_experiments/openai}"
TIMESTEPS="${2:-50000}"
BATCH_SIZE="${3:-256}"

buffers=("2048" "512")
envs=("8")

for buffer_size in "${buffers[@]}"
do
   echo "$buffer_size"
    for num_envs in "${envs[@]}"
    do
        python ppo.py \
            --output-dir ${OUT} \
            --buffer-size ${buffer_size} \
            --num-workers ${num_envs} \
            --batch-size ${BATCH_SIZE} \
            --num-timesteps ${TIMESTEPS}
    done
done
