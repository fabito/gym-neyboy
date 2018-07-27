import logging
import math

import numpy as np

import gym
from gym import spaces, utils
from gym.utils import seeding

from gym_neyboy.envs.neyboy import SyncGame, ACTION_NAMES, ACTION_LEFT, ACTION_RIGHT, GAME_OVER_SCREEN

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class NeyboyEnv(gym.Env, utils.EzPickle):
    metadata = {'render.modes': ['human', 'rgb_array']}

    def __init__(self, headless=False, score_threshold=0.95, death_reward=-1, user_data_dir=None):
        utils.EzPickle.__init__(self, headless)
        self.headless = headless
        self.scoring_threshold = score_threshold
        self.death_reward = death_reward

        self._state = None
        self.viewer = None

        self.game = SyncGame.create(headless=headless, user_data_dir=user_data_dir)
        self.game.load()
        self._update_state()

        dims = self.state.dimensions
        self.observation_space = spaces.Box(low=0, high=255, shape=(270, 450, 3), dtype=np.uint8)
        self.action_space = spaces.Discrete(len(ACTION_NAMES))

    @property
    def state(self):
        return self._state

    def _update_state(self):
        self._state = self.game.get_state()

    def step(self, a):
        self.game.resume()
        if a == ACTION_LEFT:
            self.game.tap_left()
        elif a == ACTION_RIGHT:
            self.game.tap_right()
        self._update_state()
        self.game.pause()
        is_over = self.state.status == GAME_OVER_SCREEN

        if is_over:
            reward = self.death_reward
        else:
            angle = self.state.position['angle']
            cosine = math.cos(angle)
            reward = cosine if cosine > self.scoring_threshold else 0.1
            log.debug('HiScore: {}, Score: {}, Action: {}, position_label: {}, Reward: {}, GameOver: {}'.format(
                self.state.hiscore,
                self.state.score,
                ACTION_NAMES[a],
                self.state.position['name'],
                reward,
                is_over))
        return self.state.snapshot, reward, is_over, dict(score=self.state.score, hiscore=self.state.score, position=self.state.position['angle'])

    def reset(self):
        self.game.restart()
        self._update_state()
        self.game.pause()
        return self._state.snapshot

    def render(self, mode='human', close=False):
        img = self.state.snapshot
        if mode == 'rgb_array':
            return img
        elif mode == 'human':
            from gym.envs.classic_control import rendering
            if self.viewer is None:
                self.viewer = rendering.SimpleImageViewer()
            self.viewer.imshow(img)
            return self.viewer.isopen

    def close(self):
        self.game.stop()
        super(NeyboyEnv, self).close()

    def get_action_meanings(self):
        return ACTION_NAMES

    def seed(self, seed=None):
        self.np_random, seed1 = seeding.np_random(seed)