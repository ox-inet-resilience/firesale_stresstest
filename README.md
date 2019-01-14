# Code for: Foundations of System-Wide Stress Testing

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/ox-inet-resilience/bank_contagion/master)

Note: This is a simplified version that only retains a fire sale contagion
model, but retains much of the generality of the comprehensive system-wide
stress test model.

By: J. Doyne Farmer, Alissa M. Kleinnijenhuis, Paul Nahai-Williamson, and Thom Wetzer.

The model.py file is a hybrid source code - Jupyter notebook.
There are 3 illustrative experiments:
1. Effect of price impact on systemic risk
2. Effect of initial shock on systemic risk
3. Difference between leverage targeting and threshold model (Cont-Schaanning 2017)

Data taken from 2018 EU-wide stress test results,
https://eba.europa.eu/risk-analysis-and-data/eu-wide-stress-testing/2018/results.

# Overview

### 1. Institutions

Banks:
- asset: cash, tradable asset, other asset
- liability: loan, other liability

### 2. Contracts

- Tradable
  - action: sell asset
- Loan
  - action: pay loan
- Other assets and liabilities

### 3. Constraints

- Leverage constraint
  - λ := E / A
  - Delever if λ < λ^buffer = 4%
  - Delever to λ^target = 5%
  - Default if λ < λ^min = 3%

### 4. Markets

Asset market:
- Contains an orderbook
- Price impact (Cifuentes 2005)
  - ![price impact formula](https://latex.codecogs.com/svg.latex?p'&space;=&space;p&space;\exp{\left[-\beta&space;\frac{\mathrm{sold}}{\mathrm{marketcap}}\right]})
  - β is chosen such that when 10% of the market cap is sold, the price drops by 10%.

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
