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
# # Foundations for system-wide stress testing: overlapping portfolio contagion

# + {"slideshow": {"slide_type": "slide"}, "cell_type": "markdown"}
# ## Model initialization

# + {"slideshow": {"slide_type": "subslide"}}
# %matplotlib notebook
import random
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np

from model import Model, make_plots, run_sim_set

plt.ion()
plt.rcParams['figure.figsize'] = (7.0, 4.8)
plt.style.use('ggplot')
# For reproducibility
random.seed(1337)
np.random.seed(1337)

eu = Model()

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
    eu.parameters.PRICE_IMPACTS = defaultdict(lambda: pi)

eocs, solds = run_sim_set(eu, price_impacts, set_pi)
make_plots(eocs, solds, 100 * price_impacts, 'Price impact (%)')

# + {"slideshow": {"slide_type": "slide"}, "cell_type": "markdown"}
# ## 2. Effect of initial shock on systemic risk

# + {"slideshow": {"slide_type": "-"}}
set_pi(0.01)
initial_shocks = np.linspace(0, 0.3, 21)

def set_shock(shock):
    eu.parameters.INITIAL_SHOCK = shock

eocs, solds = run_sim_set(eu, initial_shocks, set_shock)
make_plots(eocs, solds, 100 * initial_shocks, 'Initial shock (%)')


# + {"slideshow": {"slide_type": "slide"}, "cell_type": "markdown"}
# ## 3. Difference between leverage targeting and threshold model (Cont-Schaanning 2017)

# + {"slideshow": {"slide_type": "-"}}
# Threshold model (same as previous simulation)
eocs1, solds1 = run_sim_set(eu, initial_shocks, set_shock)
# Leverage targeting
# This (100% leverage buffer) makes the banks to always delever to
# reach leverage target.
eu.parameters.BANK_LEVERAGE_BUFFER = 1
eocs2, solds2 = run_sim_set(eu, initial_shocks, set_shock)

plt.figure()
plt.ylim(-0.01, 1.05)
plt.plot(100 * initial_shocks, eocs1, label='Threshold model')
plt.plot(100 * initial_shocks, eocs2, label='Leverage targeting')
plt.xlabel('Initial shock (%)')
plt.ylabel('Systemic risk $\\mathbb{E}$')
plt.legend()

plt.figure()
plt.plot(100 * initial_shocks, 100 * solds1, label='Threshold model')
plt.plot(100 * initial_shocks, 100 * solds2, label='Leverage targeting')
plt.xlabel('Initial shock (%)')
plt.ylabel('Proportion of tradable assets delevered (%)')
plt.legend()
