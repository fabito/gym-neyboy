#!/usr/bin/env python3
import multiprocessing
import sys
from time import sleep


import tensorflow as tf
from baselines import logger
from baselines.common.vec_env.vec_frame_stack import VecFrameStack
from baselines.ppo2.policies import CnnPolicy, LstmPolicy, LnLstmPolicy, MlpPolicy
from baselines.ppo2.ppo2 import Model

from cmd_util import neyboy_arg_parser, make_neyboy_env


def train(env_id, seed, policy, load_path, num_episodes, frame_skip, no_render):
    ncpu = multiprocessing.cpu_count()
    if sys.platform == 'darwin':
        ncpu //= 2
    config = tf.ConfigProto(allow_soft_placement=True,
                            intra_op_parallelism_threads=ncpu,
                            inter_op_parallelism_threads=ncpu)
    config.gpu_options.allow_growth = True  # pylint: disable=E1101
    tf.Session(config=config).__enter__()
    env = VecFrameStack(make_neyboy_env(env_id, 1, seed, allow_early_resets=True, frame_skip=frame_skip, save_obs=True), 4)

    policy = {'cnn': CnnPolicy, 'lstm': LstmPolicy, 'lnlstm': LnLstmPolicy, 'mlp': MlpPolicy}[policy]
    ob_space = env.observation_space
    ac_space = env.action_space
    ent_coef = .01
    vf_coef = 0.5
    max_grad_norm = 0.5
    model = Model(policy=policy, ob_space=ob_space, ac_space=ac_space, nbatch_act=env.num_envs,
                  nbatch_train=0,
                  nsteps=0, ent_coef=ent_coef, vf_coef=vf_coef,
                  max_grad_norm=max_grad_norm)
    model.load(load_path)
    for _ in range(num_episodes):
        observation = env.reset()
        done = False
        while not done:
            if not no_render:
                env.render()
            action, _, _, _ = model.step(observation)
            observation, reward, done, info = env.step(action)
        print(reward, done, info)    
        sleep(1)

def main():
    parser = neyboy_arg_parser()
    parser.add_argument('--policy', help='Policy architecture', choices=['cnn', 'lstm', 'lnlstm', 'mlp'], default='cnn')
    parser.add_argument('--load-path', help='load path', default=None)
    parser.add_argument('--num-episodes', type=int, default=1)
    parser.add_argument('--frame-skip', type=int, default=4)
    parser.add_argument('--no-render', default=False, action='store_true')
    args = parser.parse_args()
    logger.configure()
    train(args.env,  seed=args.seed, policy=args.policy, load_path=args.load_path, num_episodes=args.num_episodes, frame_skip=args.frame_skip, no_render=args.no_render)


if __name__ == '__main__':
    main()
