import random
from collections import defaultdict

import pylab
import numpy as np

from economicsl import Simulation

from institutions import Bank
from markets import AssetMarket
from contracts import AssetType


NBANKS = 48
def get_extent_of_systemic_event(out):
    # See Gai-Kapadia 2010
    eose = sum(out) / NBANKS
    if eose < 0.05:
        return 0
    return eose


class Parameters:
    BANK_LEVERAGE_MIN = 0.03
    BANK_LEVERAGE_BUFFER = 0.04
    BANK_LEVERAGE_TARGET = 0.05
    ASSET_TO_SHOCK = AssetType.GOV_BONDS
    INITIAL_SHOCK = 0.2
    SIMULATION_TIMESTEPS = 6
    PRICE_IMPACTS = defaultdict(lambda: 0.01)
    SIMULTANEOUS_FIRESALE = True

# + {"slideshow": {"slide_type": "subslide"}}
class Model:
    def __init__(self):
        self.simulation = None
        self.parameters = Parameters

    def get_time(self):
        return self.simulation.get_time()

    def update_asset_price(self, assetType):
        for agent in self.allAgents:
            agent.update_asset_price(assetType)

    def apply_initial_shock(self, assetType, fraction):
        """ creates an initial shock, by decreasing
            the prices on the asset market
        """
        new_price = self.assetMarket.get_price(assetType) * (1.0 - fraction)
        self.assetMarket.set_price(assetType, new_price)
        self.update_asset_price(assetType)

    def initialize(self):
        self.simulation = Simulation()
        self.allAgents = []
        self.assetMarket = AssetMarket(self)
        with open('EBA_2018.csv', 'r') as data:
            self.bank_balancesheets = data.read().strip().split('\n')[1:]
        for bs in self.bank_balancesheets:
            row = bs.split(' ')
            bank_name, CET1E, leverage, debt_sec, gov_bonds = row
            bank = Bank(bank_name, self.simulation)
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

    def run_simulation(self):
        self.apply_initial_shock(
            Parameters.ASSET_TO_SHOCK,
            Parameters.INITIAL_SHOCK)
        defaults = [0]
        total_sold = []
        while self.get_time() < Parameters.SIMULATION_TIMESTEPS:
            self.simulation.advance_time()
            self.simulation.bank_defaults_this_round = 0
            # this is an extra safeguard to ensure order independence
            random.shuffle(self.allAgents)
            # In most agent-based models, there is only step().  We
            # split it into step() and act() phases to ensure order
            # independence in some conditions. In the full model,
            # trigger_default() may contain a behavioural unit that
            # does pull funding.
            for agent in self.allAgents:
                agent.step()
            if Parameters.SIMULTANEOUS_FIRESALE:
                self.assetMarket.clear_the_market()
            for agent in self.allAgents:
                agent.act()
            defaults.append(self.simulation.bank_defaults_this_round)
            total_sold.append(
                sum(self.assetMarket.totalAmountsSold.values()) /
                sum(self.assetMarket.total_quantities.values()))
        return defaults, total_sold

# + {"slideshow": {"slide_type": "subslide"}}
# Helper function
def make_plots(eocs, solds, xarray, xlabel):
    pylab.figure()
    pylab.ylim(-0.01, 1.05)
    pylab.plot(xarray, eocs)
    pylab.xlabel(xlabel)
    pylab.ylabel('Systemic risk $\\mathbb{E}$')

    pylab.figure()
    pylab.plot(xarray, 100 * solds)
    pylab.xlabel(xlabel)
    pylab.ylabel('Proportion of tradable assets delevered (%)')

def run_sim_set(model, params, apply_param):
    eocs = []
    total_solds = []
    for param in params:
        apply_param(param)
        model.initialize()
        defaults, total_sold = model.run_simulation()
        eoc = get_extent_of_systemic_event(defaults)
        eocs.append(eoc)
        # Only use the final element of total_sold (i.e. at the
        # end of the simulation).
        total_solds.append(total_sold[-1])
    return eocs, np.array(total_solds)
