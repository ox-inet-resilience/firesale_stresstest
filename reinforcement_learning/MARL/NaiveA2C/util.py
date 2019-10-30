import matplotlib.pyplot as plt
import numpy as np

def setup_matplotlib():
    #pylab.style.use('fivethirtyeight')
    #pylab.style.use('ggplot')
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
