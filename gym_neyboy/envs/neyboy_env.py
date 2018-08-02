import math
import os

import numpy as np

import gym
from gym import spaces, utils, logger
from gym.utils import seeding

from gym_neyboy.envs.neyboy import SyncGame, ACTION_NAMES, ACTION_LEFT, ACTION_RIGHT, GAME_OVER_SCREEN, \
    DEFAULT_NAVIGATION_TIMEOUT, DEFAULT_GAME_URL


class NeyboyEnv(gym.Env, utils.EzPickle):
    metadata = {'render.modes': ['human', 'rgb_array']}

    def __init__(self, headless=None, score_threshold=0.95, death_reward=-1, stay_alive_reward=0.1, user_data_dir=None):
        utils.EzPickle.__init__(self, headless, score_threshold, death_reward)

        if headless is None:
            headless = os.environ.get('GYM_NEYBOY_ENV_NON_HEADLESS', None) is None

        self.headless = headless
        self.score_threshold = score_threshold
        self.stay_alive_reward = stay_alive_reward
        self.death_reward = death_reward

        self._state = None
        self.viewer = None

        navigation_timeout = int(os.environ.get('GYM_NEYBOY_ENV_TIMEOUT', DEFAULT_NAVIGATION_TIMEOUT))
        game_url = os.environ.get('GYM_NEYBOY_GAME_URL', DEFAULT_GAME_URL)
        browser_ws_endpoint = os.environ.get('GYM_NEYBOY_BROWSER_WS_ENDPOINT', None)

        if browser_ws_endpoint is not None:
            self.game = SyncGame.create(navigation_timeout=navigation_timeout, game_url=game_url, browser_ws_endpoint=browser_ws_endpoint)
        else:
            self.game = SyncGame.create(headless=headless, user_data_dir=user_data_dir,
                                        navigation_timeout=navigation_timeout, game_url=game_url)

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
            reward = 1.0 #cosine if cosine > self.score_threshold else self.stay_alive_reward

        logger.debug('HiScore: {}, Score: {}, Action: {}, position_label: {}, Reward: {}, GameOver: {}'.format(
            self.state.hiscore,
            self.state.score,
            ACTION_NAMES[a],
            self.state.position['name'],
            reward,
            is_over))
        return self._get_obs(), reward, is_over, dict(score=self.state.score, hiscore=self.state.score, position=self.state.position['angle'])

    def _get_obs(self):
        return self.state.snapshot

    def reset(self):
        self.game.restart()
        self._update_state()
        self.game.pause()
        return self._get_obs()

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


class NeyboyEnvAngle(NeyboyEnv):
    def __init__(self, headless=None, score_threshold=0.95, death_reward=-1, stay_alive_reward=0.1, user_data_dir=None):
        super().__init__(headless, score_threshold, death_reward, stay_alive_reward, user_data_dir)
        self.observation_space = spaces.Box(low=-1, high=1, shape=(), dtype=np.float32)

    def _update_state(self):
        self._state = self.game.get_state(include_snapshot=None)

    def _get_obs(self):
        return self.state.position['angle']
