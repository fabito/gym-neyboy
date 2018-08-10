import base64
import datetime as dt
import io

try:
    from gym import logger
except:
    import logging as logger

import random
import re
import uuid
from collections import namedtuple

import pathlib
import numpy as np
from PIL import Image
from pyppeteer import launch, connect
from syncer import sync

ACTION_NAMES = ["NOOP", "LEFT", "RIGHT"]
ACTION_NONE = 0
ACTION_LEFT = 1
ACTION_RIGHT = 2

START_SCREEN = 0
GAME_SCREEN = 1
GAME_OVER_SCREEN = 2

TOAST_APPEARANCE_FREQUENCY = 10

GameState = namedtuple('GameState',
                       ['game_id', 'id', 'score', 'status', 'hiscore', 'snapshot', 'timestamp', 'dimensions',
                        'position'])

DEFAULT_NAVIGATION_TIMEOUT = 60 * 1000
DEFAULT_GAME_URL = 'http://fabito.github.io/neyboy/'
DEFAULT_BROWSER_WS_ENDPOINT = 'ws://localhost:3000'
DEFAULT_CHROMIUM_LAUNCH_ARGS = ['--no-sandbox', '--window-size=80,315', '--disable-infobars']


class Game:

    def __init__(self, headless=True, user_data_dir=None, navigation_timeout=DEFAULT_NAVIGATION_TIMEOUT,
                 game_url=DEFAULT_GAME_URL, browser_ws_endpoint=None, initial_width=180, initial_height=320):

        self.initial_width = initial_width
        self.initial_height = initial_height
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.navigation_timeout = navigation_timeout
        self.is_running = False
        self.browser = None
        self.page = None
        self.state = None
        self._dims = None
        self.game_id = str(uuid.uuid4())
        self.state_id = 0
        self.game_url = game_url
        self.browser_ws_endpoint = browser_ws_endpoint

    async def initialize(self):
        if self.browser_ws_endpoint is not None:
            logger.info('Connecting to running instance at: %s', self.browser_ws_endpoint)
            self.browser = await connect(browserWSEndpoint=self.browser_ws_endpoint)
            self.page = await self.browser.newPage()
        else:
            logger.info('Launching new browser instance')
            if self.user_data_dir is not None:
                self.browser = await launch(headless=self.headless, userDataDir=self.user_data_dir,
                                            args=DEFAULT_CHROMIUM_LAUNCH_ARGS)
            else:
                self.browser = await launch(headless=self.headless)

            pages = await self.browser.pages()
            if len(pages) > 0:
                self.page = pages[0]
            else:
                self.page = await self.browser.newPage()

        self.page.setDefaultNavigationTimeout(self.navigation_timeout)
        await self.page.setViewport(dict(width=117, height=156))
        await self.page.goto('{}?w={}&h={}'.format(self.game_url, self.initial_width, self.initial_height),
                             {'waitUntil': 'networkidle2'})
        envjs_path = pathlib.Path(__file__).resolve().parent.joinpath('env.js')
        await self.page.addScriptTag(dict(path=str(envjs_path)))
        await self.is_ready()

    @staticmethod
    async def create(headless=True, user_data_dir=None, navigation_timeout=DEFAULT_NAVIGATION_TIMEOUT,
                     game_url=DEFAULT_GAME_URL, browser_ws_endpoint=None) -> 'Game':
        o = Game(headless, user_data_dir, navigation_timeout, game_url, browser_ws_endpoint)
        await o.initialize()
        return o

    @property
    def x(self):
        return int(self._dims['x'])

    @property
    def y(self):
        return int(self._dims['y'])

    @property
    def width(self):
        return int(self._dims['width'])

    @property
    def height(self):
        return int(self._dims['height'])

    async def dimensions(self):
        dimensions = await self.page.evaluate('''() => {
                return neyboyChallenge.dimensions();
            }''')
        return dimensions

    async def is_ready(self):
        await self.page.waitForFunction('''()=>{
            return neyboyChallenge && neyboyChallenge.isReady();
        }''')

    async def start(self):
        if random.randint(0, 1):
            await self.tap_right()
        else:
            await self.tap_left()
        await self._shuffle_toasts()
        return self

    async def _shuffle_toasts(self):
        await self.page.evaluate('''() => {
            neyboyChallenge.shuffleToasts();
        }''')
        return self

    def is_over(self):
        return self.state.status == GAME_OVER_SCREEN

    async def _wait_until_replay_button_is_active(self):
        await self.resume()
        await self.page.waitForFunction('''() => {
            return neyboyChallenge.isOver();
        }''')

    async def is_loaded(self):
        return await self.is_ready()

    async def pause(self):
        await self.page.evaluate('''() => {
            neyboyChallenge.pause();
        }''')

    async def resume(self):
        await self.page.evaluate('''() => {
            neyboyChallenge.resume();
        }''')

    async def get_score(self):
        score = await self.page.evaluate('''() => {
            return neyboyChallenge.getScore();
        }''')
        return int(score) if score else 1

    async def get_high_score(self):
        hiscore = await self.page.evaluate('''() => {
                return neyboyChallenge.runtime !== undefined &&
                       neyboyChallenge.runtime.getEventVariableByName('hiscore').data;
                }''')
        return int(hiscore) if hiscore else 1

    async def get_scores(self):
        scores = await self.page.evaluate('''() => {
                const score = neyboyChallenge.getScore();
                const hiscore = neyboyChallenge.runtime.getEventVariableByName('hiscore').data || 0;
                return {score, hiscore};
                }''')
        scores['score'] = int(scores['score'])
        scores['hiscore'] = int(scores['hiscore'])
        return scores

    async def tap_left(self, delay=0):
        x = self.x + self.width // 4
        y = self.y + self.height // 3
        await self.page.mouse.click(x, y, {'delay': delay})

    async def tap_right(self, delay=0):
        x = (self.x + self.width) - self.width // 4
        y = self.y + self.height // 3
        await self.page.mouse.click(x, y, {'delay': delay})

    async def stop(self):
        await self.browser.close()

    async def _hard_restart(self):
        await self.page.reload({'waitUntil': 'networkidle2'})
        await self.is_loaded()

    async def restart(self):
        self.game_id = str(uuid.uuid4())
        self.state_id = 0

        if self.state.status == GAME_SCREEN:
            # commit suicide

            while not self.is_over():
                logger.debug('suiciding')
                await self.tap_left()
                await self.tap_left()
                await self.tap_left()
                await self.get_state()

        if self.is_over():
            await self._wait_until_replay_button_is_active()
            x = self.x + self.width // 2
            y = self.y + self.height - self.height // 7
            await self.page.mouse.click(x, y)
        elif self.state.status == START_SCREEN:
            logger.debug('start screen')
        else:
            raise ValueError('Unknown state: {}'.format(self.state.status))

        await self.start()

    async def screenshot(self, format="jpeg", quality=30, encoding='binary'):
        dims = await self.dimensions()
        dims['y'] = dims['height'] / 2
        dims['height'] = dims['height'] - dims['y'] - 30
        snapshot = await self.page.screenshot({
            'type': format,
            'quality': quality,
            'clip': dims
        })
        if encoding == 'binary':
            return snapshot
        else:
            encoded_snapshot = base64.b64encode(snapshot)
            return encoded_snapshot.decode('ascii')

    async def get_state(self, include_snapshot='numpy'):
        """

        :param include_snapshot: numpy, pil, ascii, bytes, None
        :param fmt:
        :param quality:
        :return: a GameState instance
        """
        state = await self.page.evaluate('''(includeSnapshot, format, quality) => {
            return neyboyChallenge.state(includeSnapshot, format, quality);
        }''', include_snapshot, 'image/jpeg', 30)

        self.state_id += 1
        self._dims = state['dimensions']
        state['hiscore'] = int(state['hiscore'])
        state['score'] = int(state['score'])
        state['status'] = int(state['status'])
        state['id'] = self.state_id
        state['game_id'] = self.game_id
        state['timestamp'] = dt.datetime.today().timestamp()

        if include_snapshot is not None:
            base64_string = state['snapshot']
            base64_string = re.sub('^data:image/.+;base64,', '', base64_string)
            imgdata = base64.b64decode(base64_string)
            bytes_io = io.BytesIO(imgdata)

            if include_snapshot == 'numpy':
                image = Image.open(bytes_io)
                state['snapshot'] = np.array(image)
            elif include_snapshot == 'pil':
                image = Image.open(bytes_io)
                state['snapshot'] = image
            elif include_snapshot == 'ascii':
                image = Image.open(bytes_io)
                state['snapshot'] = self.screenshot_to_ascii(image, 0.1, 3)
            elif include_snapshot == 'bytes':
                state['snapshot'] = bytes_io
            else:
                raise ValueError('Supported snapshot formats are: numpy, pil, ascii, bytes')

        self.state = GameState(**state)

        return self.state

    async def save_screenshot(self, path, format="jpeg", quality=30):
        dims = await self.dimensions()
        dims['y'] = dims['height'] / 2
        dims['height'] = dims['height'] - dims['y'] - 30
        await self.page.screenshot({
            'path': path,
            'type': format,
            'quality': quality,
            'clip': dims
        })

    async def is_in_start_screen(self):
        playing_status = await self._get_is_playing_status()
        return playing_status == START_SCREEN

    @staticmethod
    def screenshot_to_ascii(img, scale, intensity_correction_factor, width_correction_factor=7 / 4):
        """
        https://gist.github.com/cdiener/10491632
        :return:
        """
        chars = np.asarray(list(' .,:;irsXA253hMHGS#9B&@'))
        SC, GCF, WCF = scale, intensity_correction_factor, width_correction_factor
        S = (round(img.size[0] * SC * WCF), round(img.size[1] * SC))
        img = np.sum(np.asarray(img.resize(S)), axis=2)
        img -= img.min()
        img = (1.0 - img / img.max()) ** GCF * (chars.size - 1)
        return "\n".join(("".join(r) for r in chars[img.astype(int)]))


class SyncGame:

    def __init__(self, game: Game):
        self.game = game

    def __getattr__(self, attr):
        return sync(getattr(self.game, attr))

    @staticmethod
    def create(headless=True, user_data_dir=None, navigation_timeout=DEFAULT_NAVIGATION_TIMEOUT,
               game_url=DEFAULT_GAME_URL, browser_ws_endpoint=None) -> 'SyncGame':
        o = sync(Game.create)(headless, user_data_dir, navigation_timeout, game_url, browser_ws_endpoint)
        return SyncGame(o)
