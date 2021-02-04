from gym.envs.registration import register

register(
    id='Tafl-v1',
    entry_point='gym_tafl.envs:TaflEnv',
)
