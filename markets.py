from collections import defaultdict

import numpy as np

from contracts import eps

# This represents a sale order in an asset market's orderbook.
class Order:
    def __init__(self, asset, quantity):
        self.asset = asset
        self.quantity = quantity

    def settle(self):
        # clear sale
        quantity_sold = min(self.asset.quantity, self.quantity)
        old_price = self.asset.assetMarket.oldPrices[self.asset.assetType]
        self.asset.quantity -= quantity_sold
        self.asset.putForSale_ -= quantity_sold
        # Sell the asset at the mid-point price
        value_sold = quantity_sold * (self.asset.price + old_price) / 2
        if value_sold >= eps:
            self.asset.assetParty.add_cash(value_sold)


# The key functions are clear_the_market() and compute_price_impact()
class AssetMarket:
    def __init__(self, model):
        self.model = model

        self.prices = defaultdict(lambda: 1.0)
        self.oldPrices = {}
        self.price_impacts = self.model.parameters.PRICE_IMPACTS

        # This is the quantities sold for each step
        self.quantities_sold = defaultdict(np.longdouble)
        # This is the cumulative quantities sold for each tradable asset
        # type.
        self.cumulative_quantities_sold = defaultdict(np.longdouble)
        # The total market cap of the system.
        self.total_quantities = defaultdict(np.longdouble)
        self.orderbook = []

    def put_for_sale(self, asset, quantity):
        assert quantity > 0, quantity
        self.orderbook.append(Order(asset, quantity))
        atype = asset.get_asset_type()
        self.quantities_sold[atype] += quantity
        if not self.model.parameters.SIMULTANEOUS_FIRESALE:
            self.clear_the_market()

    def clear_the_market(self):
        self.oldPrices = dict(self.prices)
        # 1. Update price based on price impact
        for atype, v in self.quantities_sold.items():
            self.compute_price_impact(atype, v)

            newPrice = self.prices[atype]
            priceLost = self.oldPrices[atype] - newPrice
            if priceLost > 0:
                self.model.update_asset_price(atype)
            self.cumulative_quantities_sold[atype] += v
        self.quantities_sold = defaultdict(np.longdouble)

        # 2. Perform the sale
        for order in self.orderbook:
            order.settle()
        self.orderbook = []

    def compute_price_impact(self, assetType, qty_sold):
        current_price = self.prices[assetType]
        price_impact = self.price_impacts[assetType]
        total = self.total_quantities[assetType]
        if total <= 0:
            return

        fraction_sold = qty_sold / total

        # See Cifuentes 2005 for the choice of the price impact
        # function.
        # Exponential price impact. `beta` is chosen such that
        # when 5% of the market cap is sold, the price drops by
        # 5%.
        beta = -1 / 0.05 * np.log(1 - price_impact)
        new_price = current_price * np.exp(-fraction_sold * beta)
        self.set_price(assetType, new_price)

    def get_price(self, assetType):
        return self.prices[assetType]

    def set_price(self, assetType, newPrice):
        self.prices[assetType] = newPrice
