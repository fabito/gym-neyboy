from gym.envs.registration import register

register(
    id='neyboy-v0',
    entry_point='gym_neyboy.envs:NeyboyEnv',
)
# register(
#     id='foo-extrahard-v0',
#     entry_point='gym_foo.envs:FooExtraHardEnv',
# )