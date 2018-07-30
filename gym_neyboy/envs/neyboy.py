import base64
import datetime as dt
import io
import logging
import random
import re
import uuid
from collections import namedtuple
from time import sleep

import numpy as np
from PIL import Image
from pyppeteer import launch
from syncer import sync


ACTION_NAMES = ["NOOP", "LEFT", "RIGHT"]
ACTION_NONE = 0
ACTION_LEFT = 1
ACTION_RIGHT = 2


START_SCREEN = 0
GAME_SCREEN = 1
GAME_OVER_SCREEN = 2

EASTER_EGG_APPEARANCE_FREQUENCY = 10

GameState = namedtuple('GameState',
                       ['game_id', 'id', 'score', 'status', 'hiscore', 'snapshot', 'timestamp', 'dimensions',
                        'position'])


DEFAULT_NAVIGATION_TIMEOUT = 60 * 1000

class Game:

    def __init__(self, headless=True, user_data_dir=None, navigation_timeout=DEFAULT_NAVIGATION_TIMEOUT):
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.navigation_timeout = navigation_timeout
        self.is_running = False
        self.browser = None
        self.page = None
        self.state = None
        self.game_id = str(uuid.uuid4())
        self.state_id = 0

    async def initialize(self):
        if self.user_data_dir is not None:
            self.browser = await launch(headless=self.headless, userDataDir=self.user_data_dir, args=['--no-sandbox'])
        else:
            self.browser = await launch(headless=self.headless, args=['--no-sandbox'])

        pages = await self.browser.pages()
        if len(pages) > 0:
            self.page = pages[0]
        else:
            self.page = await self.browser.newPage()

        self.page.setDefaultNavigationTimeout(self.navigation_timeout)


    @staticmethod
    async def create(headless=True, user_data_dir=None, navigation_timeout=DEFAULT_NAVIGATION_TIMEOUT) -> 'Game':
        o = Game(headless, user_data_dir, navigation_timeout)
        await o.initialize()
        return o

    async def dimensions(self):
        # Get dimensions of the canvas element
        dimensions = await self.page.evaluate('''() => {
                const iframe = document.getElementsByTagName("iframe")[0];
                let {x, y, width, height} = iframe.getBoundingClientRect();
                return {x, y, width, height};
            }''')
        return dimensions

    async def is_loaded(self):
        await self.page.waitForFunction('''() => {
            const iframe = document.getElementsByTagName("iframe")[0];
            const iframeWindow = iframe.contentWindow;
            return iframeWindow.cr_getC2Runtime !== undefined &&
                   iframeWindow.cr_getC2Runtime().tickcount > 200;
        }''')

    async def is_over(self):
        animation_name = await self._get_is_playing_status()
        return animation_name == GAME_OVER_SCREEN

    async def _get_is_playing_status(self):
        """
        :return: 0 for start_screen, 1 for game_screen and 2 for game_over_screen
        """
        is_playing = await self.page.evaluate('''() => {
                const iframe = document.getElementsByTagName("iframe")[0];
                const iframeWindow = iframe.contentWindow;
                return iframeWindow.cr_getC2Runtime !== undefined &&
                       iframeWindow.cr_getC2Runtime().getEventVariableByName('isPlaying').data;
                }''')
        return int(is_playing)

    async def _get_cur_animation_name(self):
        animation_name = await self.page.evaluate('''() => {
                const iframe = document.getElementsByTagName("iframe")[0];
                const iframeWindow = iframe.contentWindow;
                return iframeWindow.cr_getC2Runtime !== undefined &&
                       iframeWindow.cr_getC2Runtime().getLayerByName('Game').instances[3].cur_animation.name;
                }''')
        return animation_name

    async def load(self):
        await self.page.goto('https://neyboy.com.br', {'waitUntil': 'networkidle2'})
        await self.is_loaded()
        return self

    async def start(self):
        if random.randint(0, 1):
            await self.tap_right()
        else:
            await self.tap_left()
        # await self.page.click('iframe.sc-htpNat')
        return self

    async def pause(self):
        await self.page.evaluate('''() => {
            const iframe = document.getElementsByTagName("iframe")[0];
            const iframeWindow = iframe.contentWindow;
            iframeWindow.cr_setSuspended(true);
        }''')
        self.is_running = False
        return self

    async def resume(self):
        await self.page.evaluate('''() => {
            const iframe = document.getElementsByTagName("iframe")[0];
            const iframeWindow = iframe.contentWindow;
            iframeWindow.cr_setSuspended(false);
        }''')
        self.is_running = True
        return self

    async def get_score(self):
        score = await self.page.evaluate('''() => {
            const iframe = document.getElementsByTagName("iframe")[0];
            const iframeWindow = iframe.contentWindow;
            const score = iframeWindow.cr_getC2Runtime().getLayerByName('Game').instances[4].text;
            return score;
        }''')
        return int(score) if score else 1

    async def get_high_score(self):
        hiscore = await self.page.evaluate('''() => {
                const iframe = document.getElementsByTagName("iframe")[0];
                const iframeWindow = iframe.contentWindow;
                return iframeWindow.cr_getC2Runtime !== undefined &&
                       iframeWindow.cr_getC2Runtime().getEventVariableByName('hiscore').data;
                }''')
        return int(hiscore) if hiscore else 1

    async def get_scores(self):
        scores = await self.page.evaluate('''() => {
                const iframe = document.getElementsByTagName("iframe")[0];
                const iframeWindow = iframe.contentWindow;
                const runtime = iframeWindow.cr_getC2Runtime();
                const score = runtime.getLayerByName('Game').instances[4].text || 0;
                const hiscore = runtime.getEventVariableByName('hiscore').data || 0;
                return {score, hiscore};
                }''')
        scores['score'] = int(scores['score'])
        scores['hiscore'] = int(scores['hiscore'])
        return scores

    async def tap_right(self, delay=0):
        await self.page.mouse.click(470, 500, {'delay': delay})
        # FIXME Investigate why pressing arrow keys aren't working
        # await self.page.keyboard.press('ArrowRight', {'text': 'd', 'delay': delay})
        # await self.page.keyboard.press("d", {'text': 'd', 'delay': delay})

    async def tap_left(self, delay=0):
        await self.page.mouse.click(200, 500, {'delay': delay})
        # await self.page.keyboard.press('ArrowLeft', {'text': 'a', 'delay': delay})

    async def stop(self):
        await self.browser.close()

    async def wait_until_replay_button_is_active(self):
        await self.resume()
        await self.page.waitForFunction('''() => {
            const iframe = document.getElementsByTagName("iframe")[0];
            const iframeWindow = iframe.contentWindow;
            if (iframeWindow.cr_getC2Runtime) {
                const modal = iframeWindow.cr_getC2Runtime().getLayerByName('modal');
                replay = modal.instances[0]
                if (replay.behavior_insts) {
                    return replay.behavior_insts[0].active;
                }
            }
            return false;
        }''')

    async def restart(self):
        logging.debug('Restarting game')
        self.game_id = str(uuid.uuid4())
        self.state_id = 0
        playing_status = await self._get_is_playing_status()
        if playing_status == START_SCREEN:
            logging.debug('Start screen')
        # elif playing_status == 1:  # game is running
        #     logging.debug('')
        elif playing_status == GAME_OVER_SCREEN:  # game over
            await self.wait_until_replay_button_is_active()
            logging.debug('Replay button active')
            sleep(0.5)
            await self.page.mouse.click(400, 525)
        else:
            await self.page.reload({'waitUntil': 'networkidle2'})
            await self.is_loaded()

        await self.start()

    async def _click(self, x, y):
        await self.page.mouse.click(x, y)

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

    @staticmethod
    def _normalize_angle(position):
        angle = float(position['angle'])
        if 6.5 > angle >= 4.5:
            angle = max((angle - 6.3) / 1.5, -1)
        elif 1.8 > angle > 0:
            angle = min(angle / 1.5, 1)
        position['angle'] = angle

    async def get_state(self, include_snapshot='numpy', fmt='image/jpeg', quality=30, crop=True):
        """

        :param include_snapshot: numpy, pil, ascii, bytes, None
        :param fmt:
        :param quality:
        :return:
        """
        self.state_id += 1
        state = await self.page.evaluate('''(includeSnapshot, format, quality) => {
            return new Promise((resolve, reject) => {
                const iframe = document.getElementsByTagName('iframe')[0];
                const {x, y, width, height} = iframe.getBoundingClientRect();
                const dimensions = {x, y, width, height};
                const iframeWindow = iframe.contentWindow;
                const runtime = iframeWindow.cr_getC2Runtime();
                const gameLayer = runtime.getLayerByName('Game');
                const score = gameLayer.instances[4].text || 0;
                const hiscore = runtime.getEventVariableByName('hiscore').data || 0;
                const inst3 = gameLayer.instances[3];
                const position = {
                    name: inst3.animTriggerName,
                    angle: inst3.angle
                };                
                const status = runtime.getEventVariableByName('isPlaying').data;

                if (includeSnapshot) {
                    iframeWindow['cr_onSnapshot'] = function(snapshot) {
                        resolve({score, hiscore, snapshot, status, dimensions, position});
                    }
                    iframeWindow.cr_getSnapshot(format, quality);
                } else {
                    const snapshot = null;
                    resolve({score, hiscore, snapshot, status, dimensions, position});
                }
            })
        }''', include_snapshot, fmt, quality)

        state['hiscore'] = int(state['hiscore'])
        state['score'] = int(state['score'])
        state['status'] = int(state['status'])
        state['id'] = self.state_id
        state['game_id'] = self.game_id
        state['timestamp'] = dt.datetime.today().timestamp()

        position = state['position']
        self._normalize_angle(position)
        state['position'] = position

        if include_snapshot is not None:
            dims = state['dimensions']
            x = 0
            y = dims['height'] / 2
            height = dims['height'] - y - 30
            width = dims['width']
            base64_string = state['snapshot']
            base64_string = re.sub('^data:image/.+;base64,', '', base64_string)
            imgdata = base64.b64decode(base64_string)

            bytes_io = io.BytesIO(imgdata)
            image = Image.open(bytes_io)

            if crop:
                image = image.crop((x, y, x + width, y + height))

            if include_snapshot == 'numpy':
                state['snapshot'] = np.array(image)
            elif include_snapshot == 'pil':
                state['snapshot'] = image
            elif include_snapshot == 'ascii':
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
    def create(headless=True, user_data_dir=None, navigation_timeout=60) -> 'SyncGame':
        o = sync(Game.create)(headless, user_data_dir, navigation_timeout)
        return SyncGame(o)
