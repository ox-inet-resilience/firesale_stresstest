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
# ---

from actions import SellAsset, PayLoan, eps


class AssetType:
    CORPORATE_BONDS = 1
    GOV_BONDS = 2


class Contract:
    ctype = 'Contract'

    def __init__(self, assetParty, liabilityParty):
        self.assetParty = assetParty
        self.liabilityParty = liabilityParty

    def get_action(self, me):
        return None

    def is_eligible(self, me):
        return False

    def get_asset_party(self):
        return self.assetParty

    def get_liability_party(self):
        return self.liabilityParty

    def get_name(self, me):
        return ''


class Tradable(Contract):
    ctype = 'Tradable'

    def __init__(self, assetParty, assetType, assetMarket, quantity):
        super().__init__(assetParty, None)
        self.assetType = assetType
        self.assetMarket = assetMarket
        self.price = self.get_market_price()
        self.quantity = quantity
        self.putForSale_ = 0.0

    def get_action(self, me):
        return SellAsset(self.assetParty, self)

    def is_eligible(self, me):
        return self.quantity > self.putForSale_

    def clear_sale(self, quantity_sold):
        quantity_sold = min(quantity_sold, self.quantity)
        old_price = self.assetMarket.oldPrices[self.assetType]
        self.quantity -= quantity_sold
        self.putForSale_ -= quantity_sold
        # Sell the asset at the mid-point price
        value_sold = quantity_sold * (self.price + old_price) / 2
        if value_sold >= eps:
            self.assetParty.add_cash(value_sold)

    def get_market_price(self):
        return self.assetMarket.get_price(self.assetType)

    def update_price(self):
        self.price = self.get_market_price()

    def get_asset_type(self):
        return self.assetType

    def get_value(self):
        return self.quantity * self.price


class Other(Contract):
    ctype = 'Other'

    def __init__(self, assetParty, liabilityParty, amount):
        super().__init__(assetParty, liabilityParty)
        self.principal = amount

    def get_value(self):
        return self.principal


class Loan(Contract):
    ctype = 'Loan'

    def __init__(self, assetParty, liabilityParty, principal):
        super().__init__(assetParty, liabilityParty)
        self.principal = principal

    def reduce_principal(self, amount):
        self.principal -= amount

    def get_action(self, me):
        return PayLoan(self.liabilityParty, self)

    def is_eligible(self, me):
        return self.get_value() > 0

    def get_value(self):
        return self.principal
