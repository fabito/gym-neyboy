#!/usr/bin/env python3
import multiprocessing
import sys

import tensorflow as tf
from baselines import logger
from baselines.common.vec_env.vec_frame_stack import VecFrameStack
from baselines.ppo2 import ppo2
from baselines.ppo2.policies import CnnPolicy, LstmPolicy, LnLstmPolicy, MlpPolicy

from cmd_util import neyboy_arg_parser, make_neyboy_env


def train(env_id, learning_rate, num_epoch, buffer_size, batch_size, num_timesteps, num_workers, seed, policy, load_path):
    ncpu = multiprocessing.cpu_count()
    if sys.platform == 'darwin':
        ncpu //= 2
    config = tf.ConfigProto(allow_soft_placement=True,
                            intra_op_parallelism_threads=ncpu,
                            inter_op_parallelism_threads=ncpu)
    config.gpu_options.allow_growth = True  # pylint: disable=E1101
    tf.Session(config=config).__enter__()

    env = VecFrameStack(make_neyboy_env(env_id, num_workers, seed), 4)
    policy = {'cnn': CnnPolicy, 'lstm': LstmPolicy, 'lnlstm': LnLstmPolicy, 'mlp': MlpPolicy}[policy]
    nsteps = buffer_size // num_workers
    nminibatches = buffer_size // batch_size
    ppo2.learn(policy=policy, env=env, nsteps=nsteps, nminibatches=nminibatches,
               lam=0.95, gamma=0.99, noptepochs=num_epoch, log_interval=1,
               ent_coef=.01,
               lr=lambda f: f * learning_rate,
               cliprange=lambda f: f * 0.1,
               total_timesteps=int(num_timesteps * 1.1),
               save_interval=10, load_path=load_path)


def main():
    parser = neyboy_arg_parser()
    parser.add_argument('--policy', help='Policy architecture', choices=['cnn', 'lstm', 'lnlstm', 'mlp'], default='cnn')
    parser.add_argument('--num-workers', type=int, default=8)
    parser.add_argument('--buffer-size', type=int, default=1024)
    parser.add_argument('--batch-size', type=int, default=512)
    parser.add_argument('--num-epoch', type=int, default=4)
    parser.add_argument('--lr', type=float, default=2.5e-4)
    parser.add_argument('--load-path', help='load path', default=None)
    args = parser.parse_args()
    logger.configure()
    train(args.env, learning_rate=args.lr, num_epoch=args.num_epoch, buffer_size=args.buffer_size, batch_size=args.batch_size, num_timesteps=args.num_timesteps, seed=args.seed, num_workers=args.num_workers, policy=args.policy, load_path=args.load_path)


if __name__ == '__main__':
    main()
