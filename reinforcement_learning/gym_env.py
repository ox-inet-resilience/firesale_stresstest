from collections import defaultdict
import random
import pylab
import numpy as np

from economicsl import Simulation

from behaviours import pay_off_liabilities, sell_assets_proportionally
from institutions import Bank, DefaultException
from markets import AssetMarket
from model import Model

class RLBank(Bank):
    def choose_actions(self):
        # 0) If I'm insolvent, default.
        if self.is_insolvent():
            raise DefaultException(self, 'SOLVENCY')
        balance = self.get_cash_()
        # 1. Pay off liabilities to delever
        deLever = min(balance, self.leverageConstraint.get_amount_to_delever())
        if deLever > 0:
            deLever = pay_off_liabilities(self, deLever)
            balance -= deLever

        # 2. Raise liquidity to delever later
        if balance < deLever:
            amount_to_raise = (deLever - balance) * random.random()
            sell_assets_proportionally(self, amount_to_raise)

class RLModel(Model):
    def initialize(self):
        self.simulation = Simulation()
        self.allAgents = []
        self.assetMarket = AssetMarket(self)
        with open('EBA_2018.csv', 'r') as data:
            self.bank_balancesheets = data.read().strip().split('\n')[1:]
        for bs in self.bank_balancesheets:
            row = bs.split(' ')
            bank_name, CET1E, leverage, debt_sec, gov_bonds = row
            bank = RLBank(bank_name, self.simulation)
            debt_sec = float(debt_sec)
            gov_bonds = eval(gov_bonds)
            CET1E = float(CET1E)
            corp_bonds = debt_sec - gov_bonds
            asset = CET1E / (float(leverage) / 100)
            cash = 0.05 * asset
            liability = asset - CET1E
            other_asset = asset - debt_sec - cash
            loan = other_liability = liability / 2
            bank.init(
                self, self.assetMarket,
                assets=(cash, corp_bonds, gov_bonds, other_asset),
                liabilities=(loan, other_liability))
            self.allAgents.append(bank)

    def step(self):
        self.simulation.advance_time()
        self.simulation.bank_defaults_this_round = 0
        random.shuffle(self.allAgents)
        for agent in self.allAgents:
            agent.step()
        if self.parameters.SIMULTANEOUS_FIRESALE:
            self.assetMarket.clear_the_market()
        for agent in self.allAgents:
            agent.act()
        return sum(agent.get_ledger().get_equity_valuation() for agent in self.allAgents)

if __name__ == '__main__':
    random.seed(1337)
    np.random.seed(1337)
    eu = RLModel()
    eu.parameters.PRICE_IMPACTS = defaultdict(lambda: 0.05)
    eu.initialize()
    eu.apply_initial_shock(
        eu.parameters.ASSET_TO_SHOCK,
        eu.parameters.INITIAL_SHOCK)
    episode_reward = 0
    while eu.get_time() < eu.parameters.SIMULATION_TIMESTEPS:
        reward = eu.step()
        episode_reward += reward
    print("Episode reward", episode_reward)
