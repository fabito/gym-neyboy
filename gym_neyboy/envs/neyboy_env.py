import numpy as np

import gym
from gym import error, spaces, utils

from gym_neyboy.envs.neyboy import SyncGame, ACTION_NAMES, ACTION_LEFT, ACTION_RIGHT, GAME_OVER_SCREEN, \
    EASTER_EGG_APPEARANCE_FREQUENCY


class NeyboyEnv(gym.Env, utils.EzPickle):
    metadata = {'render.modes': ['human', 'rgb_array']}

    def __init__(self, headless=True, frame_skip=2.5, scoring_reward=1, death_reward=-1, stay_alive_reward=0.01,
                 easter_egg_reward=5, user_data_dir=None):
        gym.Env.__init__(self)
        self.headless = headless
        self.frame_skip = frame_skip
        self.stay_alive_reward = stay_alive_reward
        self.death_reward = death_reward
        self.scoring_reward = scoring_reward
        self.easter_egg_reward = easter_egg_reward
        self._state = None
        self.viewer = None

        self.game = SyncGame.create(headless=headless, user_data_dir=user_data_dir)
        self.game.load()
        self._update_state()

        dims = self._state.dimensions
        self.observation_space = spaces.Box(low=0, high=255, shape=(dims['height'], dims['width'], 3), dtype=np.uint8)
        self.action_space = spaces.Discrete(len(ACTION_NAMES))

    def _update_state(self):
        self._state = self.game.get_state()

    def step(self, a):
        reward = 0.0
        score_before_action = self._state.score
        is_over = False
        self.game.resume()
        if a == ACTION_LEFT:
            self.game.tap_left()
        elif a == ACTION_RIGHT:
            self.game.tap_right()
        # sleep(self.frame_skip / 10)
        self._update_state()
        # self.game.pause()
        if self._state.status == GAME_OVER_SCREEN:
            reward = self.death_reward
            is_over = True
        else:
            if self._state.score > score_before_action:
                reward = self.scoring_reward
            else:
                reward = self.stay_alive_reward + self._state.score / 1000

            if (self._state.score % EASTER_EGG_APPEARANCE_FREQUENCY) == 0:
                reward += self.easter_egg_reward * self._state.score / EASTER_EGG_APPEARANCE_FREQUENCY

        return self._state.snapshot, reward, is_over, dict(score=self._state.score, hiscore=self._state.score)

    def reset(self):
        self.game.restart()
        self._update_state()
        self.game.pause()
        return self._state.snapshot

    def render(self, mode='human', close=False):
        img = self.game.screenshot()
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

