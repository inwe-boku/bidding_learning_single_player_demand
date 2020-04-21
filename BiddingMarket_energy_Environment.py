# -*- coding: utf-8 -*-
"""
Created on Wed Mar  4 10:05:34 2020

@author: Viktor
"""

#### Environment für 2 Player#####



import gym
from gym import spaces
import numpy as np
from collections import deque
from market_clearing import market_clearing, converter, combine_sold_quantities


#C = 30
#CAP = 300
#env = EnMarketEnv02(CAP = np.array([100,100]), costs = 30)

#env.observation_space.shape[:]
#env.action_space.shape[0]-1

class BiddingMarket_energy_Environment(gym.Env):
    
    """
    Energy Market environment for OpenAI gym
    
    """
    metadata = {'render.modes': ['human']}   ### ?

    def __init__(self, CAP, costs, Fringe=0, Rewards=0, Split=0, past_action = 1, Agents = 3):              
        super(BiddingMarket_energy_Environment, self).__init__()
        
        self.CAP = CAP
        self.costs = costs
        self.Fringe = Fringe
        self.Rewards = Rewards
        self.Split = Split
        self.past_action = past_action
        self.Agents = Agents
        
        # Continous action space for bids
        self.action_space = spaces.Box(low=np.array([0]), high=np.array([10000]), dtype=np.float16)
        
        # fit observation_space size to choosen environment settings
        x = 1 + self.Agents*2
        if self.Fringe == 1:
            x = x + self.fringe.shape[0]
        if past_action == 0:
            x = 1 + self.Agents
        
        if self.Split == 1:
            self.action_space = spaces.Box(low=np.array([0,0,0]), high=np.array([10000,10000,10000]), dtype=np.float16)
            x = 1+ self.Agents*3 + self.Agents
            if self.Fringe == 1:
                x = x + self.fringe.shape[0]
            if self.past_action == 0:
                x = 1+ self.Agents*3
        
        # set observation space   
        self.observation_space = spaces.Box(low=0, high=10000, shape=(x,1), dtype=np.float16)
        
        # Discrete Demand opportunities are missing yet
        
        # Reward Range
        self.reward_range = (0, 1000000)

    
    def set_up_agents(self, action, last_action, nmb_agents):
        """
        Sets Up all the Agents to act as Suppliers on Energy Market
        Supplier: Agent Number (int), their own Capacity, their Action, their cost, again their Capacity
        output is on big 2 dimensional np.array containing all Suppliers (optional: + fringe Players)
    
        """
        
        suppliers = [0]*nmb_agents
        
        for n in range(nmb_agents):
            a1 = action[n,0]
            suppliers[n] = [int(n), self.CAP[n], a1, self.costs[n], self.CAP[n]]
            
            if self.Split == 1:
                a1,a2,a3 = action[n]
                suppliers[n] = [int(n), self.CAP[n], a1, a2, a3, self.costs[n], self.CAP[n]]
                
        
        np.asarray(suppliers)
        
        if self.Fringe == 1:
            suppliers = np.concatenate([suppliers, self.fringe])
        
        return suppliers
        
    def _next_observation(self, last_action, nmb_agents):
        
        """
        Set Up State
        State includes: Demand, Capacitys of all Players, sort by from lowest to highest last Actions of all Players (Optional)
    
        """
        #Q = np.array([500, 1000, 1500])
        #Q = np.random.choice(Q)
        
        Q = np.random.randint(900, 1100, 1)
        obs = np.array([Q[0]])
        
        for n in range(nmb_agents):
            obs = np.append(obs, self.CAP[n])
            
        if self.past_action == 1:
            la1 = last_action.flatten()
            obs = np.insert(obs, nmb_agents+1, la1)
                
            if self.Fringe == 1:
                obs = np.concatenate([obs, self.fringe[:,2]])   ## last actions fringe

        return  obs


    def step(self, action, last_action):
        
        self.current_step += 1
        
        # get current state        
        obs = self._next_observation(last_action, self.Agents)
        Demand = obs[0]
        q = obs[0]
        
        # set up all the agents as suppliers in the market
        all_suppliers = self.set_up_agents(action, last_action, self.Agents)
        
        # market_clearing: orders all suppliers from lowest to highest bid, 
        # last bid of cumsum offerd capacitys determines the price; also the real sold quantities are derived
        # if using splits, convert them in the right shape for market_clearing-function 
        # and after that combine sold quantities of the same supplier again
        if self.Split == 0:
            market = market_clearing(q, all_suppliers)
            sold_quantities = market[2]
        else:
            all_suppliers_split = converter(all_suppliers, self.Agents)
            market = market_clearing(q, all_suppliers_split)
            sold_quantities = market[2]
            sold_quantities = combine_sold_quantities(sold_quantities, self.Agents)

        market_price = market[0]
        
        # caluclate rewards
        reward = self.reward_function(all_suppliers, sold_quantities, market_price, self.Agents, self.Rewards)
        
     

        # Render Commands 
        self.safe(action, self.current_step)
        
        self.last_q = Demand
        self.sum_q += Demand
        self.avg_q = self.sum_q/self.current_step
        
        self.last_bids = action
        self.sum_action += action
        self.avg_action = self.sum_action/self.current_step
        
        self.last_rewards = reward
        self.sum_rewards += reward
        self.avg_rewards = self.sum_rewards/self.current_step
        
        # save last actions for next state (= next obeservation)
        last_action = action
        np.sort(last_action)
        
        if self.Split == 1:            ### needs to skip evry third argument ## evtl. nach oben zu if schreiben
            last_action = [0]*self.Agents
            for n in range(self.Agents):
                last_action[n] = action[n,0:2]
            np.asarray(last_action)
            np.sort(last_action)  ## not True, should sort by lowest of row and than by lowest column

        #### DONE and next_state
        done = self.current_step == 128 
        obs = self._next_observation(last_action, self.Agent)
        


        return obs, reward, done, {}
    
    
    def safe(self, action, current_step):
        # to save all actions during one round
        Aktionen = (action, current_step)
        self.AllAktionen.append(Aktionen)
        
    def reward_function(self, suppliers, sold_quantities, p, nmb_agents, Penalty):
        '''
        Different Options of calculating the Reward
        Rewards = 0: Default, Reward is (price-costs)*acceptedCAP 
        Rewards = 1: Reward is (price-costs)*acceptedCAP - (price*unsoldCAP)
        Rewards = 2: Reward is ((price-costs)*acceptedCAP)/(cost*maxCAP)
        Rewards = 3 (= combination of 1 and 2): Reward is ((price-costs)*acceptedCAP - (price*unsoldCAP))/(cost*maxCAP)
        # Reward 4 only works without Splits
        Rewards = 4: Reward is (Reward 1)/((ownBid-cost)*maxCAP)
        
        '''
        reward = [0]*nmb_agents
        
        for n in range(nmb_agents):
            reward[n] = (p - suppliers[n,3]) * sold_quantities[n]
        np.asarray(reward)


        if Penalty == 1:
            for n in range(nmb_agents):
                reward[n] = reward[n] - (suppliers[n,3]*(suppliers[n,4] - sold_quantities[n]))       
        
        if Penalty == 2:
            for n in range(nmb_agents):
                reward[n] = reward[n] / (suppliers[n,3] * suppliers[n,4])       
            
        if Penalty == 3:
            for n in range(nmb_agents):
                reward[n] = reward[n] - (suppliers[n,3]*(suppliers[n,4] - sold_quantities[n]))
                reward[n] = reward[n] / (suppliers[n,3] * suppliers[n,4]) 
          
        if Penalty == 4:
            for n in range(nmb_agents):
                reward[n] = reward[n] - (suppliers[n,3]*(suppliers[n,4] - sold_quantities[n]))
                #expWin = Suppliers[n,2]  * sold_quantities[n] # Alternative!!
                expWin = (suppliers[n,2] - suppliers[n,3]) * sold_quantities[n] #auskommentiern wenn mit alternative
                expWin = np.clip(expWin, 0.0000001, 10000000)
                reward[n] = reward [n] /expWin
                if self.Split == 1:
                    break
                print('ERROR: only works without Split')
                

        return reward
    
    def reset(self):
        # Reset the state of the environment to an initial state
        self.current_step = 0
        self.avg_action = 0
        self.sum_action = 0
        self.sum_q = 0
        self.sum_rewards = 0
        self.AllAktionen = deque(maxlen=500)
        self.start_action = np.zeros(self.Agents)
        
        if self.Split == 1:
            self.start_action = np.zeros(self.Agents*3)
       
        if self.Fringe == 1:
            #Fringe or Strategic Player
            #        # Test move to init
            #Readout fringe players from other.csv (m)
            #Readout fringe players from other.csv (m)
            read_out = np.genfromtxt("others.csv",delimiter=";",autostrip=True,comments="#",skip_header=1,usecols=(0,1))
            
            #Readout fringe switched to conform with format; finge[0]=quantity fringe[1]=bid
            self.fringe = np.fliplr(read_out)
            self.fringe = np.pad(self.fringe,((0,0),(1,2)),mode='constant', constant_values=(2, 0))
            
            if self.Split == 1:
                self.fringe = np.pad(self.fringe,((0,0),(1,3)),mode='constant', constant_values=(2, 0)) 
            #self.fringe = np.pad(self.fringe,((0,0),(1,0)),mode='constant')
        
        return self._next_observation(self.start_action, self.Agents)
    
    def render(self, mode='human', close=False):
        # Render the environment to the screen
        print(f'Step: {self.current_step}')
        print(f'AllAktionen: {self.AllAktionen}')
        print(f'Last Demand of this Episode: {self.last_q}')
        print(f'Last Bid of this Episode: {self.last_bids}')
        print(f'Last Reward of this Episode: {self.last_rewards}')
        print(f'Average Demand: {self.avg_q}')
        print(f'Average Bid: {self.avg_action}')
        print(f'Average Reward: {self.avg_rewards}')
        
        