#!/usr/bin/env python3

import argparse
import uuid
from time import sleep

import gym
from asciimatics.screen import Screen
from baselines.common.atari_wrappers import MaxAndSkipEnv, ScaledFloatFrame
from baselines import logger
import gym_neyboy
from neyboy_wrappers import ObservationSaver,  ObservationSaver2, ObservationSaver3, VerticallyFlipFrame


def main(screen, args):
    game_id = str(uuid.uuid4())
    logger.configure('.tmp/{}/{}_'.format(args.frame_skip, game_id))
    env = gym.make('neyboy-v1')
    env2 = gym.make('neyboy-v1')
    env3 = gym.make('neyboy-v1')
    env4 = gym.make('neyboy-v1')
    env = MaxAndSkipEnv(env, skip=args.frame_skip)
    env = ObservationSaver(env, stage_name='max_skip')
    # env = VerticallyFlipFrame(env)
    # env = ObservationSaver2(env, stage_name='vflip')
    # env = ScaledFloatFrame(env)
    # env = ObservationSaver3(env, stage_name='scaled')

    env.reset()
    done = False
    total_reward = 0
    total_steps = 0
    while not done:
        total_steps += 1
        ev = screen.get_key()
        action = 0
        if ev in (Screen.KEY_LEFT, ord('A'), ord('a')):
            action = 1
        elif ev in (Screen.KEY_RIGHT, ord('D'), ord('d')):
            action = 2
        observation, reward, done, info = env.step(action)
        total_reward += reward
        screen.print_at('{0:.2f}'.format(reward), 0, 0)
        screen.print_at('{0:.2f}'.format(total_reward), 0, 1)
        screen.print_at('done: {}'.format(done), 0, 2)
        screen.refresh()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--frame-skip', type=int, default=4)
    args = parser.parse_args()
    Screen.wrapper(main, arguments=[args])
