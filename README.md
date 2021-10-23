# tafl-gym

The TaflEnv is an [OpenAI gym](https://gym.openai.com/) environment for reinforcement learning. In particular, it
implements the two-players, asymmetric, turn-based zero-sum board game
of [Hnefatafl](https://en.wikipedia.org/wiki/Tafl_games). The environment defaults to the Tablut variant, but this can
be easily changed by the user.

## Installation

You can install this environment by:

1. Downloading the repo: `git clone https://github.com/gallorob/tafl-gym`
2. Move in the repo's root folder: `cd tafl-gym`
3. Installing the requirements: `pip install -r requirements.txt`
4. Installing the environment: `pip install -e .`

## Citations

Please use the bibtex below if you want to cite this repository in your publications:

```
@misc{tafl-gym,
  author = {Gallotta Roberto},
  title = {OpenAI Gym environment based on the Tafl board games for Reinforcement Learning},
  year = {2021},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/gallorob/tafl-gym}},
}
```

This Gym Environment was developed for and used in "Tafl-ES: Exploring Evolution Strategies for Asymmetrical Board Games" (to appear in post-proceedings of AIxIA 2021):
```
@inproceedings{
  series = {Lecture {Notes} in {Artificial} {Intelligence} ({LNAI})},
  title = {Tafl-{ES}: {Exploring} {Evolution} {Strategies} for {Asymmetrical} {Board} {Games}},
  abstract = {NeuroEvolution Strategies (NES) are a subclass of Evolution Strategies (ES). While their application to games and board games have been studied in the past, current state of the art in most of the games is still held by classic RL models, such as AlphaGo Zero. This is despite recent work showing their desirable properties. In this paper we use NES applied to the board game Hnefatafl, a known hard environment given its asymmetrical nature. In the experiment we set up we coevolve two populations of intelligent agents. With results collected thus far we show the validity of this approach and useful techniques to overcome its large computation resource and time requirements.},
  date = {2021},
  publisher = {Springer Verlag},
  author = {Gallotta, Roberto and Capobianco, Roberto},
}
```

## Balances and search space
### Custom variant

Measured balance using random agents:
```
Summary after running 1000 games on "custom":
Attacker won 317/1000 games (31.7%)
Defender won 373/1000 games (37.3%)
Draws were 310/1000 games (31.0%)
Average number of legal moves per turn: 36.14
Average number of moves per match: 73.96
```

### Tablut

Measured balance using random agents:

```
Summary after running 1000 games on "tablut":
Attacker won 195/1000 games (19.5%)
Defender won 402/1000 games (40.2%)
Draws were 403/1000 games (40.3%)
Average number of legal moves per turn: 82.46
Average number of moves per match: 92.82
```
