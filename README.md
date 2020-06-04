# Code for: Foundations of System-Wide Stress Testing

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/ox-inet-resilience/firesale_stresstest/master)

Note: This is a simplified version that only retains a fire sale contagion
model, but retains much of the generality of the comprehensive system-wide
stress test model.

By: J. Doyne Farmer, Alissa M. Kleinnijenhuis, Paul Nahai-Williamson, and Thom Wetzer.

For questions, contact alissa.kleinnijenhuis＠maths.ox.ac.uk (note: the "@" symbol is from unicode U+FF20 and so needs to be replaced with @).

The model.py file is a hybrid source code - Jupyter notebook.
There are 3 illustrative experiments:
1. Effect of price impact on systemic risk
2. Effect of initial shock on systemic risk
3. Difference between leverage targeting and threshold model (Cont-Schaanning 2017)

Data taken from 2018 EU-wide stress test results,
https://eba.europa.eu/risk-analysis-and-data/eu-wide-stress-testing/2018/results.

# Usage

Requires Python 3.
1. `pip install -r requirements.txt`
2. Comment out the line `pylab.ion()` in simulation.py
3. Add `pylab.show()` at the end of simulation.py
4. `python3 simulation.py`

To run the model in a Jupyter notebook:
1. `pip install -r requirements.txt`
2. Edit `~/.jupyter/jupyter_notebook_config.py` and add this line `c.NotebookApp.contents_manager_class = 'jupytext.TextFileContentsManager'  # noqa`. This is to make sure that model.py can be read as a jupyter notebook
3. `jupyter notebook`
4. Execute all the cells in simulation.py

If you want to display model.py in the form of a slideshow, you must do `pip install RISE && jupyter-nbextension install rise --py --sys-prefix && jupyter-nbextension enable rise --py --sys-prefix`.

# Overview

The framework consist of 5 building blocks: institutions, contracts, constraints, markets, and behaviours.
The simple asset-sale model fills in the 5 building blocks as follows:

### 1. Institutions

1. Banks  
   Each bank has a balance sheet consisting of the following components:
   - asset: cash, tradable asset, other asset
   - liability: loan, other liability

### 2. Contracts

Tradable assets T interconnect the banks.
The cash C, other assets O and the generic liability L do not.
- Tradable
  - action: sell asset
- Loan
  - action: pay loan
- Other assets and liabilities

### 3. Constraints

Each bank faces a leverage constraint.

- Leverage constraint
  - λ := E / A
  - Delever if λ < λ^buffer = 4%
  - Delever to λ^target = 5%
  - Default if λ < λ^min = 3%  
    When this happens, all tradable assets of a defaulted bank are liquidated.

### 4. Markets

The price of each tradable asset p_m is determined using a price impact function.
The price is a function of the net cumulative number of asset sales.
Each asset has its own price impact parameter, which determines the market liquidity of the asset.

Asset market:
- Contains an orderbook
- Price impact (Cifuentes 2005)
  - ![price impact formula](https://latex.codecogs.com/svg.latex?p'&space;=&space;p&space;\exp{\left[-\beta&space;\frac{\mathrm{sold}}{\mathrm{marketcap}}\right]})
  - By default, β is chosen such that when 5% of the market cap is sold, the price drops by 5%.

### 5. Behaviours

Bank only acts to avoid default, by de-levering to a leverage target if its
buffer has been breached. It does this by selling tradable asset proportionally
and paying bank liabilities proportionally.

# References
1. Cont, Rama, and Eric Schaanning. "Fire sales, indirect contagion and systemic stress testing." (2017).
   https://dx.doi.org/10.2139/ssrn.2541114
2. Cifuentes, R., Ferrucci, G. and Shin, H. S. "Liquidity risk and contagion." Journal of the European Economic Association 3(2-3), 556–566. (2005).
   https://dx.doi.org/10.2139/ssrn.824166
3. Greenwood, Robin, Augustin Landier, and David Thesmar. "Vulnerable banks." Journal of Financial Economics 115, no. 3: 471-485. (2015).
   https://doi.org/10.3386/w18537
4. Gai, Prasanna, and Sujit Kapadia. "Contagion in financial networks." In Proceedings of the Royal Society of London A: Mathematical, Physical and Engineering Sciences, p. rspa20090410. The Royal Society. (2010).
   https://doi.org/10.1098/rspa.2009.0410
