#!/usr/bin/env python3

import argparse

import gym
from asciimatics.screen import Screen

import gym_neyboy


def main(screen, args):
    env = gym.make('neyboy-v0')
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
        screen.refresh()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    Screen.wrapper(main, arguments=[args])
