# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.3'
#       jupytext_version: 0.8.6
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
#   livereveal:
#     autolaunch: true
#     scroll: true
# ---

# + {"slideshow": {"slide_type": "slide"}, "cell_type": "markdown"}
# # Bank contagion

# + {"slideshow": {"slide_type": "slide"}, "cell_type": "markdown"}
# ## Model initialization

# + {"slideshow": {"slide_type": "subslide"}}
# %matplotlib notebook
import random
from collections import defaultdict

import pylab
import numpy as np

from economicsl import Simulation

from agents import Bank, AssetMarket
from contracts import AssetType


pylab.ion()
pylab.rcParams['figure.figsize'] = (7.0, 4.8)
pylab.style.use('ggplot')
# For reproducibility
random.seed(1337)
np.random.seed(1337)
NBANKS = 48


def get_extent_of_systemic_event(out):
    return sum(out) / NBANKS


class Parameters:
    BANK_LEVERAGE_MIN = 0.03
    BANK_LEVERAGE_BUFFER = 0.05
    BANK_LEVERAGE_TARGET = 0.07
    ASSET_TO_SHOCK = AssetType.GOV_BONDS
    INITIAL_SHOCK = 0.2
    SIMULATION_TIMESTEPS = 6
    PRICE_IMPACTS = defaultdict(lambda: 0.05)

# + {"slideshow": {"slide_type": "subslide"}}
class Model:
    def __init__(self):
        self.simulation = None

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
        self.parameters = Parameters
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

    def run_schedule(self):
        self.apply_initial_shock(
            Parameters.ASSET_TO_SHOCK,
            Parameters.INITIAL_SHOCK)
        defaults = [0]
        total_sold = []
        while self.get_time() < Parameters.SIMULATION_TIMESTEPS:
            self.simulation.advance_time()
            self.simulation.bank_defaults_this_round = 0
            random.shuffle(self.allAgents)
            for agent in self.allAgents:
                agent.step()
            self.assetMarket.clear_the_market()
            for agent in self.allAgents:
                agent.act()
            defaults.append(self.simulation.bank_defaults_this_round)
            total_sold.append(sum(self.assetMarket.totalAmountsSold.values()))
        return defaults, total_sold


# + {"slideshow": {"slide_type": "slide"}}
eu = Model()

# Helper function
def run_sim_set(params, apply_param):
    eocs = []
    total_solds = []
    for param in params:
        apply_param(param)
        eu.initialize()
        defaults, total_sold = eu.run_schedule()
        eoc = get_extent_of_systemic_event(defaults)
        eocs.append(eoc)
        # Only use the final element of total_sold (i.e. at the
        # end of the simulation).
        total_solds.append(total_sold[-1])
    return eocs, np.array(total_solds)


# Helper function
def make_plots(eocs, solds, xarray, xlabel):
    pylab.figure()
    pylab.ylim(-0.01, 1.05)
    pylab.plot(xarray, eocs)
    pylab.xlabel(xlabel)
    pylab.ylabel('Systemic risk $\\mathbb{E}$')

    pylab.figure()
    pylab.plot(xarray, solds / 1000)
    pylab.xlabel(xlabel)
    pylab.ylabel('Total firesale (euro bln)')


# + {"slideshow": {"slide_type": "slide"}, "cell_type": "markdown"}
# # Simulations
# 1. Effect of price impact on systemic risk
# 2. Effect of initial shock on systemic risk
# 3. Difference between leverage targeting and threshold model (Cont-Schaanning 2017)

# + {"slideshow": {"slide_type": "slide"}, "cell_type": "markdown"}
# ## 1. Effect of price impact on systemic risk

# + {"slideshow": {"slide_type": "-"}}
price_impacts = np.linspace(0, 0.1, 21)

def set_pi(pi):
    Parameters.PRICE_IMPACTS = defaultdict(lambda: pi)

eocs, solds = run_sim_set(price_impacts, set_pi)
make_plots(eocs, solds, 100 * price_impacts, 'Price impact (%)')

# + {"slideshow": {"slide_type": "slide"}, "cell_type": "markdown"}
# ## 2. Effect of initial shock on systemic risk

# + {"slideshow": {"slide_type": "-"}}
Parameters.PRICE_IMPACTS = defaultdict(lambda: 0.05)
initial_shocks = np.linspace(0, 0.3, 21)

def set_shock(shock):
    Parameters.INITIAL_SHOCK = shock

eocs, solds = run_sim_set(initial_shocks, set_shock)
make_plots(eocs, solds, 100 * initial_shocks, 'Initial shock (%)')


# + {"slideshow": {"slide_type": "slide"}, "cell_type": "markdown"}
# ## 3. Difference between leverage targeting and threshold model (Cont-Schaanning 2017)

# + {"slideshow": {"slide_type": "-"}}
# Threshold model (same as previous simulation)
eocs1, solds1 = run_sim_set(initial_shocks, set_shock)
# Leverage targeting
Parameters.BANK_LEVERAGE_BUFFER = 1
eocs2, solds2 = run_sim_set(initial_shocks, set_shock)

pylab.figure()
pylab.ylim(-0.01, 1.05)
pylab.plot(100 * initial_shocks, eocs1, label='Threshold model')
pylab.plot(100 * initial_shocks, eocs2, label='Leverage targeting')
pylab.xlabel('Initial shock (%)')
pylab.ylabel('Systemic risk $\\mathbb{E}$')
pylab.legend()

pylab.figure()
pylab.plot(100 * initial_shocks, solds1 / 1000, label='Threshold model')
pylab.plot(100 * initial_shocks, solds2 / 1000, label='Leverage targeting')
pylab.xlabel('Initial shock (%)')
pylab.ylabel('Total firesale (euro bln)')
pylab.legend()
