import os

import gym
from baselines import logger
from baselines.bench import Monitor
from baselines.common import set_global_seeds
from baselines.common.atari_wrappers import MaxAndSkipEnv, wrap_deepmind
from baselines.common.cmd_util import arg_parser
from baselines.common.vec_env.subproc_vec_env import SubprocVecEnv

import gym_neyboy


def make_neyboy_environment(env_id, seed=0, rank=0, allow_early_resets=False, frame_skip=4):
    env = gym.make(env_id)
    env = MaxAndSkipEnv(env, skip=frame_skip)
    env.seed(seed + rank)
    env = Monitor(env, logger.get_dir() and os.path.join(logger.get_dir(), str(rank)), allow_early_resets=allow_early_resets)
    return env


def make_neyboy_env(env_id, num_env, seed, wrapper_kwargs=None, start_index=0, allow_early_resets=False, frame_skip=4):
    """
    Create a wrapped, monitored SubprocVecEnv for Neyboy.
    """
    if wrapper_kwargs is None:
        wrapper_kwargs = {}

    def make_env(rank):
        def _thunk():
            env = make_neyboy_environment(env_id, seed, rank, allow_early_resets, frame_skip=frame_skip)
            return wrap_deepmind(env, episode_life=False, clip_rewards=False)
        return _thunk

    set_global_seeds(seed)
    return SubprocVecEnv([make_env(i + start_index) for i in range(num_env)])


def wrap_neyboy_dqn(env):
    from baselines.common.atari_wrappers import wrap_deepmind
    return wrap_deepmind(env, episode_life=False, clip_rewards=False, frame_stack=True, scale=True)


def neyboy_arg_parser():
    """
    Create an argparse.ArgumentParser for run_neyboy.py.
    """
    parser = arg_parser()
    parser.add_argument('--env', help='environment ID', default='neyboy-v0')
    parser.add_argument('--seed', help='RNG seed', type=int, default=0)
    parser.add_argument('--num-timesteps', type=int, default=int(10e6))

    return parser
