import os
import threading
from pathlib import Path
import random
import cv2
import gym
import numpy as np
from PIL import Image
from baselines import logger
from gym import spaces


class InfoLogger(gym.Wrapper):
    def __init__(self, env):
        gym.Wrapper.__init__(self, env)

    def step(self, action):
        obs, reward, done, info = self.env.step(action)

        if done:
            logger.logkv_mean('action_mean', action)
            logger.logkv('action', action)

            if 'score' in info:
                score = info['score']
                logger.logkv_mean('score_mean', score)
                logger.logkv('score', score)

            logger.dumpkvs()

        return obs, reward, done, info

    def reset(self, **kwargs):
        return self.env.reset(**kwargs)


class ObservationSaver(gym.ObservationWrapper):
    def __init__(self, env, stage_name):
        gym.ObservationWrapper.__init__(self, env)
        self.stage_name = stage_name
        self.counter = 0

    @staticmethod
    def _save(obs, stage_name, counter):
        log_dir = logger.get_dir()
        data_dir = Path(log_dir, 'observations')
        data_dir.mkdir(exist_ok=True)
        obs = cv2.cvtColor(obs, cv2.COLOR_BGR2RGB)
        cv2.imwrite(str(Path(data_dir, '{}_{}.jpg'.format(stage_name, counter))), obs)

    def observation(self, frame):
        self.counter += 1
        self._save(frame, self.stage_name, self.counter)
        # threading.Thread(target=self._save, args=(frame, self.stage_name, self.counter)).start()
        return frame


class ObservationSaver2(ObservationSaver):
    pass


class ObservationSaver3(ObservationSaver):
    pass


class VerticallyFlipFrame(gym.Wrapper):
    def __init__(self, env):
        """Warp frames to 84x84 as done in the Nature paper and later work."""
        gym.Wrapper.__init__(self, env)
        self.percentage_chance = 0.5
        # self.width = 84
        # self.height = 84
        # self.observation_space = spaces.Box(low=0, high=255,
        #                                     shape=(self.height, self.width, 1), dtype=np.uint8)

    def preprocess(self, frame):
        # Convert BGR to HSV
        # hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # # define range of blue color in HSV
        # lower_green = np.array([56, 100, 100])
        # upper_green = np.array([76, 255, 255])
        # mask = cv2.inRange(hsv, lower_green, upper_green)
        # kernel = np.ones((6, 6), np.uint8)
        # morph = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        # #   morph = cv2.erode(mask, kernel,iterations = 1)
        # #   morph = cv2.dilate(mask,kernel,iterations = 1)
        # thres = cv2.threshold(morph, 127, 255, 0)[1]
        # squared = cv2.resize(thres, (84, 84), interpolation=cv2.INTER_AREA)
        # frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        # frame = cv2.resize(frame, (self.width, self.height), interpolation=cv2.INTER_AREA)
        frame = cv2.flip(frame, 0)
        return frame

    def step(self, action):

        obs, reward, done, info = self.env.step(action)

        if random.random() < self.percentage_chance:
            print('aaa')

        if action == 1:
            return 2
        if action == 2:
            return 1
        return action


        frame = cv2.flip(frame, 1)
        return frame

    def action(self, action):
        if action == 1:
            return 2
        if action == 2:
            return 1
        return action
