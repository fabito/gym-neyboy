#!/usr/bin/env python3
import argparse
import os

import gym
from asciimatics.renderers import ColourImageFile, ImageFile
from asciimatics.screen import Screen
import gym_neyboy


def main(screen, args):

    os.environ['GYM_NEYBOY_ENV_NON_HEADLESS'] = '1'
    env = gym.make(args.env)
    total_reward = 0
    total_steps = 0
    done = False
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

        # if args.color:
        #     renderer = ColourImageFile(screen, observation, height=args.height)
        # else:
        #     renderer = ImageFile(observation, height=args.height, colours=screen.colours)
        #
        # image, colours = renderer.rendered_text
        # for (i, line) in enumerate(image):
        #     screen.centre(line, i, colour_map=colours[i])

        screen.print_at('{0:.2f}'.format(reward), 0, 0)
        screen.print_at('{0:.2f}'.format(total_reward), 0, 1)
        screen.print_at('done: {}'.format(done), 0, 2)

        screen.refresh()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--env', help='environment ID', default='neyboy-v0')
    parser.add_argument('--color', action='store_true', default=False, help="Enable colors")
    parser.add_argument('--non-headless', action='store_true', default=False, help="Enable colors")
    parser.add_argument('--height', type=int, default=30, help="Screen height")
    args = parser.parse_args()
    Screen.wrapper(main, arguments=[args])
