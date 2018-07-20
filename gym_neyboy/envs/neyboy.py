import base64
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
import datetime as dt

ACTION_NAMES = ["none", "left", "right"]
ACTION_NONE = 0
ACTION_LEFT = 1
ACTION_RIGHT = 2

# 0 for start_screen
START_SCREEN = 0
# 1 for game_screen
GAME_SCREEN = 1
# 2 for game_over_screen
GAME_OVER_SCREEN = 2

EASTER_EGG_APPEARANCE_FREQUENCY = 10

GameState = namedtuple('GameState',
                       ['game_id', 'id', 'score', 'status', 'hiscore', 'snapshot', 'timestamp', 'dimensions'])


class Game:

    def __init__(self, headless=True, user_data_dir=None):
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.is_running = False
        self.browser = None
        self.page = None
        self.state = None
        self.game_id = str(uuid.uuid4())
        self.state_id = 0

    async def initialize(self):
        if self.user_data_dir is not None:
            self.browser = await launch(headless=self.headless, userDataDir=self.user_data_dir)
        else:
            self.browser = await launch(headless=self.headless)
        self.page = await self.browser.newPage()

    @staticmethod
    async def create(headless=True, user_data_dir=None) -> 'Game':
        o = Game(headless, user_data_dir)
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
            # FIXME find out why the whataspp icon is clicked sporadically
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

    async def get_state(self, include_snapshot=True, fmt='image/jpeg', quality=30):
        # TODO add game status to state
        self.state_id += 1
        state = await self.page.evaluate('''(includeSnapshot, format, quality) => {
            return new Promise((resolve, reject) => {
                const iframe = document.getElementsByTagName('iframe')[0];
                const {x, y, width, height} = iframe.getBoundingClientRect();
                const dimensions = {x, y, width, height};
                const iframeWindow = iframe.contentWindow;
                if (includeSnapshot) {
                    iframeWindow['cr_onSnapshot'] = function(snapshot) {
                        const runtime = iframeWindow.cr_getC2Runtime();
                        const score = runtime.getLayerByName('Game').instances[4].text || 0;
                        const hiscore = runtime.getEventVariableByName('hiscore').data || 0;
                        const status = runtime.getEventVariableByName('isPlaying').data;
                        resolve({score, hiscore, snapshot, status, dimensions});
                    }
                    iframeWindow.cr_getSnapshot(format, quality);
                } else {
                        const runtime = iframeWindow.cr_getC2Runtime();
                        const score = runtime.getLayerByName('Game').instances[4].text || 0;
                        const hiscore = runtime.getEventVariableByName('hiscore').data || 0;
                        const status = runtime.getEventVariableByName('isPlaying').data;
                        const snapshot = null;
                        resolve({score, hiscore, status, snapshot, dimensions});
                }
            })
        }''', include_snapshot, fmt, quality)

        state['hiscore'] = int(state['hiscore'])
        state['score'] = int(state['score'])
        state['status'] = int(state['status'])
        state['id'] = self.state_id
        state['game_id'] = self.game_id
        state['timestamp'] = dt.datetime.today().timestamp()

        if include_snapshot:
            dims = state['dimensions']
            x = 0
            y = dims['height'] / 2
            height = dims['height'] - y - 30
            width = dims['width']
            base64_string = state['snapshot']
            base64_string = re.sub('^data:image/.+;base64,', '', base64_string)
            imgdata = base64.b64decode(base64_string)
            image = Image.open(io.BytesIO(imgdata))
            state['snapshot'] = np.array(image.crop((x, y, x + width, y + height)))

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


class SyncGame:

    def __init__(self, game: Game):
        self.game = game

    @staticmethod
    def create(headless=True, user_data_dir=None) -> 'SyncGame':
        o = sync(Game.create)(headless, user_data_dir)
        return SyncGame(o)

    def dimensions(self):
        return sync(self.game.dimensions)()

    def is_loaded(self):
        return sync(self.game.is_loaded)()

    def is_over(self):
        return sync(self.game.is_over)()

    def load(self):
        return sync(self.game.load)()

    def start(self):
        return sync(self.game.start)()

    def pause(self):
        return sync(self.game.pause)()

    def resume(self):
        return sync(self.game.resume)()

    def get_score(self):
        return sync(self.game.get_score)()

    def get_scores(self):
        return sync(self.game.get_scores)()

    def get_high_score(self):
        return sync(self.game.get_high_score())()

    def tap_right(self, delay=0):
        return sync(self.game.tap_right)(delay)

    def tap_left(self, delay=0):
        return sync(self.game.tap_left)(delay)

    def stop(self):
        return sync(self.game.stop)()

    def restart(self):
        return sync(self.game.restart)()

    def _click(self, x, y):
        return sync(self.game._click)(x, y)

    def screenshot(self, format="jpeg", quality=30, encoding='binary'):
        # reconstruct image as an numpy array
        img_bytes = sync(self.game.screenshot)(format, quality, encoding)
        img = Image.open(io.BytesIO(img_bytes))
        return np.array(img)

    def get_state(self, include_snapshot=True, fmt='image/jpeg', quality=30):
        return sync(self.game.get_state)(include_snapshot, fmt, quality)
