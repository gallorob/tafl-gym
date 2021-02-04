# tafl-gym

The TaflEnv is an [OpenAI gym](https://gym.openai.com/) environment for reinforcement learning. In particular, it
implements the two-players, asymmetric, turn-based zero-sum board game
of [Hnefatafl](https://en.wikipedia.org/wiki/Tafl_games). The environment defaults to the Tablut variant, but this can
be easily changed by the user.

## Installation

You can install this environment by:

1. Downloading the repo: `git clone https://github.com/gallorob/gym-tablut.git`
2. Move in the repo's root folder: `cd gym-tablut`
3. Installing the requirements: `pip install -r requirements.txt`
4. Installing the environment: `pip install -e .`

## Citations

Please use the bibtex below if you want to cite this repository in your publications:

```
@misc{gym-tablut,
  author = {Gallotta Roberto},
  title = {OpenAI gym environment based on the Tablut board game for Reinforcement Learning},
  year = {2020},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/gallorob/gym-tablut}},
}
```
