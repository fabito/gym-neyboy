# gym-neyboy

This is an openai gym environment for the HTML5 game: [Neyboy Challenge](https://neyboy.com.br).

## neyboy-v0


<img align="right" width="180" height="320" src="https://i.imgur.com/RRTW263.gif">


Maximize your score in the [Neyboy Challenge](https://neyboy.com.br).
In this environment, the observation is an RGB image of the screen, which is an array of shape (156, 117, 3)
There are only 3 possible actions:

* 0 - Noop
* 1 - Left
* 2 - Right


The game is controlled through Pyppeteer (a Puppeteer Python port), which launches instances of the Chromium web browser.
