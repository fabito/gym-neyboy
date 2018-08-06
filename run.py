from time import sleep

from gym_neyboy.envs.neyboy import CompositeGame


def main():

    game = CompositeGame.create(headless=False)
    game.add()
    game.load(num_games=2)
    game.add()

    print(game.games)

    sleep(5)

    for g in game.games:
        g.tap_left()
        g.tap_right()
        g.tap_left()
        g.tap_right()
        g.tap_left()
        g.tap_right()
        g.tap_left()
        g.tap_right()
        g.tap_left()
        g.tap_right()
        g.tap_left()
        g.tap_right()

if __name__ == '__main__':
    main()