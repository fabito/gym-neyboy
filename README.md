# gym-neyboy

The Neyboy Challenge environment.


```
export GYM_NEYBOY_ENV_NON_HEADLESS=1 && \
export OPENAI_LOG_FORMAT=stdout,log,csv,tensorboard && \
export OPENAI_LOGDIR=/mnt/hdd/neyboy_experiments/openai/`date +%Y%m%d_%H%M%S`/ && \
python ppo.py
```