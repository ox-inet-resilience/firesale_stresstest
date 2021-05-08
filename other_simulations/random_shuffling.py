from collections import defaultdict
import random
import matplotlib.pyplot as plt
import numpy as np

from model import Model, run_sim_set

# This simulation is a benchmark of simultaneous batching of firesale action
# and random shuffling

NSIM = 100

eu = Model()

# For reproducibility
def seed():
    random.seed(1337)
    np.random.seed(1337)

def run_repeated_sim_sets(eu, params, apply_param):
    eocs_set = []
    total_solds_set = []
    for i in range(NSIM):
        eocs, total_solds = run_sim_set(eu, params, apply_param)
        eocs_set.append(eocs)
        total_solds_set.append(total_solds)
    eocs_set = np.array(eocs_set)
    total_solds_set = np.array(total_solds_set)
    aeocs = eocs_set.mean(axis=0)
    std_eocs = eocs_set.std(axis=0)
    atotal_solds = total_solds_set.mean(axis=0)
    std_total_solds = total_solds_set.std(axis=0)
    return aeocs, std_eocs, atotal_solds, std_total_solds

def setup_matplotlib():
    #plt.style.use('fivethirtyeight')
    #plt.style.use('ggplot')
    from cycler import cycler

    _cmap = plt.get_cmap('tab20')
    _cycler = (
        cycler(color=[_cmap(i / 10) for i in range(10)] + [_cmap(3 / 12), _cmap(5 / 12)]) +
        cycler(marker=[4, 5, 6, 7, 'd', 'o', '.', 4, 5, 6, 7, 'd'])
    )
    plt.rc('axes', prop_cycle=_cycler, titlesize='xx-large', grid=True, axisbelow=True)
    plt.rc('grid', linestyle=':')
    plt.rc('figure', titlesize='xx-large')
    plt.rc('savefig', dpi=200)
    return _cycler
setup_matplotlib()

def plot_custom_errorbar_plot(x, y, std, use_marker=True, color=None, marker=None, label=''):
    if color is None:
        ax = plt.gca()
        _cc = next(ax._get_lines.prop_cycler)
        color, marker = _cc.values()
    if use_marker:
        l, = plt.plot(
            x, y, marker=marker,
            markerfacecolor='none', color=color, label=label)
    else:
        l, = plt.plot(x, y, marker=',', color=color, label=label)
    y = np.array(y)
    std = np.array(std)
    plt.fill_between(x, y - std, y + std, color=color, alpha=0.4)
    return l

def make_plots(out, xarray, xlabel, label=''):
    aeocs, std_eocs, atotal_solds, std_total_solds = out
    plt.ylim(-0.02, 1.05)
    plot_custom_errorbar_plot(xarray, aeocs, std_eocs, label=label)
    plt.xlabel(xlabel)
    plt.ylabel('Systemic risk $\\mathbb{E}$')


price_impacts = np.linspace(0, 0.1, 21)
def set_pi(pi):
    eu.parameters.PRICE_IMPACTS = defaultdict(lambda: pi)

print("Running the simulation")
plt.figure()
seed()
out = run_repeated_sim_sets(eu, price_impacts, set_pi)
make_plots(out, 100 * price_impacts, 'Price impact (%)', 'simultaneous')

seed()  # reset the seed
eu.parameters.SIMULTANEOUS_FIRESALE = False
out = run_repeated_sim_sets(eu, price_impacts, set_pi)
make_plots(out, 100 * price_impacts, 'Price impact (%)', 'random shuffle')
plt.legend(loc='best')
plt.title(f'NSIM = {NSIM}')
plt.savefig(f'plots/random_shuffling_benchmark-{NSIM}.png')
plt.savefig(f'plots/random_shuffling_benchmark-{NSIM}.eps')
