# Bidding-Learning
Implementations of the Deep Q-Learning Algorithms for Auctions.

## What should it do?

- Generally, the algorithm sets up a reinforcement learning algorithm in an user defined environment,
that represents energy market auctions. The user defines number of players, their production costs & capacities as well as learning related hyper parameters of specifities of the bidding rules. Then the algorithm trains the players and outputs statistics about their behavior during training.

- Specifically, if run in the standard settings the algorithm learns in a simple predefined environment that is a minimal working example. It is chosen to be easy to understand and for comparability while debbuging.

## What is the Minimum Working Example? What do the standard settings implement?

The Minimal Working Example implements an easy market situation. Specifically:
- There is only a single learning player, while the remaining market is represented as non-learning "fringe player".
- The learning player always bids his whole capacity and is aware of the bids in the last round.
- The fringe player always submits the bids specified in the simple_fringe.csv file.
- Essentially, the first unit of energy is sold for free. Every extra unit of energy is sold for an extra 1000 price.
- The demand is predefined to equal to 5.
- The strategic player has 0 costs and 1 unit capaciy.
- The market price without the players participation is 4000. If the player bids all capacity at 0, this reduces the price to 3000. We would expect that the player can gain by becoming the price setting player and offering between 3001-3999.
- Tie breaking may be relevant. Currently the in case of tie the player with lower number gets everything. Proper tie breaking is involved to program.

Unfortunately, the learning player always learns to play 0. We would expect him to bid 3001-3999 but can not achieve it in this setting. This is the current main problem.

## Requirements

- PyTorch
- Gym
- numpy-groupies (relatively non-standard package that allows to do things similar to pandas groupby in numpy)

- it is recommended to use a package manager (PIP/Conda)
- Windows users might consider using Anaconda Navigator for package managment

## How to run?

- Clone to local repository
- run test_main.py in standard settings (or with appropriate parameters)

### How to customize a run of the algorithm?

#### Environment Parameters

The following parameters can be defined by the user by specifying them as inputs to the Environment in BiddingMarket_energy_Environment.py. This is usually done via test_main.py but can be done directly.

BiddingMarket_energy_Environment(CAP = capacitys, costs = costs, Demand =[5,6], Agents = 1,                                       Fringe = 1, Rewards = 0, Split = 0, past_action= 1, lr_actor = 1e-4, lr_critic = 1e-3, Discrete = 0)

- CAP: np.array [cap1,...,capN]             (requires elements matching number of agents) ... Generation capacity an agent can sell 
- costs: np.array [costs1,...,costsN]       (requires elements matching number of agents) ... Generation capacity an agent can sell 
- Demand: np.array [minDemand,maxDemand-1]  (2elements) ... Range of demand. Fixed demand D is written as [D,D+1]
- Agents: integer ... Number of learning players
- Fringe: binary  ... Strategic-Fringe on/off (i.e. a non-learning player submitting constant bids defined by a csv-file)
- Rewards: integer ... different reward functions, set 0 for (price-costs) * sold_quantity
- Split: binary ... Allow offering capacity at 2 different price on/off
- past_action: binary ... include the agents last actions as observations for learning on/off
- lr_actor: float < 1 .... learning rate actor network, weighs relevance of new and old experiences
- lr_critic: float < 1 .... learning rate critic network, weighs relevance of new and old experiences
- Discrete: binary ... discrete state space on/off (not ready yet)

The output mode is hardcoded in the function render belonging to BiddingMarket_energy_Environment

#### Fringe Player

The fringe player reads his bids from a csv-file. The name of the file is hardcoded in the reset function from BiddingMarket_energy_Environment.py. Currently, we provide two standard test csv:

- others.csv (non-trivial, Test Case by Christoph Graf, for comparision with optimization solver, 60 bids)
- simple_fringe.csv (easy file, price_bids increase by 1000, quantity_bids increase by 1, 60 bids)

Attention, only csv with 60 bids are compatible!

#### Test Parameters

The noise model and its variants is hard-coded in test_main.py.
There is:
- OU-Noise
- Gaussian Noise (Standard): sigma defines variance

#### Network Architecture

The architecture of the actor and critic netowrks are hardcoded in model_main.py

## Dependency Structure:

  - test_main.py                                                            (High-level interface thaht accepts user input)
      - DDPG_main.py                                                            (Learning Algorithm,        3rd Party Code)
          - model_main.py                                      (Provides Neural Networks, Actor and Critic, 3rd Party Code)
      - BiddingMarket_energy_Environment.py   (Energy Market Envrionment, receives bids from agents and determines outcome)
          - market_clearing.py                                         (Numpy based,Clears bids and demand, outputs reward)
          - other.csv, simple_fringe.csv                                         (Fixed Bidding Patterns for fringe player)
      - utils_main.py                                              (Provides Noise Models, Learning Memory, 3rd Party Code)
      - utils_2split.py                                (Provides bid-reshaping, if capacity can be split into several bids)