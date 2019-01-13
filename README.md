# Code for: Foundations of System-Wide Stress Testing

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/rht/bank_contagion/master)

Note: This is a simplified version that only retains a fire sale contagion
model, but retains much of the generality of the comprehensive system-wide
stress test model.

By: J. Doyne Farmer, Alissa M. Kleinnijenhuis, Paul Nahai-Williamson, and Thom Wetzer.

The model.py file is a hybrid source code - Jupyter notebook.
There are 3 illustrative experiments:
1. Effect of price impact on systemic risk
2. Effect of initial shock on systemic risk
3. Difference between leverage targeting and threshold model (Cont-Schaanning 2017)

# Overview

### Institutions

Banks:
- asset: cash, tradable asset, other asset
- liability: loan, other liability

### Contracts

- Tradable
  - action: sell asset
- Loan
  - action: pay loan
- Other assets and liabilities

### Constraints

- Leverage constraint
  - λ := E / A
  - Delever if λ < λ^buffer = 4%
  - Delever to λ^target = 5%
  - Default if λ < λ^min = 3%

### Markets

Asset market:
- Contains an orderbook
- Price impact
  - ![price impact formula](https://latex.codecogs.com/svg.latex?p'&space;=&space;p&space;\exp{\left[-\beta&space;\frac{\mathrm{sold}}{(\mathrm{market\%2Ccap})}\right]})
  - β is chosen such that when 10% of the market cap is sold, the price drops by 10%.

### Behaviours

Bank only acts to avoid default, by de-levering to a leverage target if its
buffer has been breached. It does this by selling tradable asset proportionally
and paying bank liabilities proportionally.

# References
1. Cont, Rama, and Eric Schaanning. "Fire sales, indirect contagion and systemic stress testing." (2017).
   https://dx.doi.org/10.2139/ssrn.2541114
2. Cifuentes, R., Ferrucci, G. and Shin, H. S. (2005), ‘Liquidity risk and contagion’, Journal of the European Economic Association 3(2-3), 556–566.
   https://dx.doi.org/10.2139/ssrn.824166
