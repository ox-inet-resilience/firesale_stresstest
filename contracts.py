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

from economicsl import Action
# floating point tolerance, ~0.001 EUR
eps = 1e-9

# All `Action` must have `perform()` and `get_max()`

class SellAsset(Action):
    def __init__(self, me, asset):
        super().__init__(me)
        self.asset = asset

    def perform(self):
        if self.asset.price <= eps:
            return
        quantity = self.get_amount() / self.asset.price
        if abs(quantity) <= eps:
            # do not perform if quantity is effectively 0
            return
        # put for sale. This is not sold immediately to ensure order
        # independence.
        self.asset.putForSale_ += quantity
        self.asset.assetMarket.put_for_sale(self.asset, quantity)

    def get_max(self):
        available_qty = self.asset.quantity - self.asset.putForSale_
        return available_qty * self.asset.price


class PayLoan(Action):
    def __init__(self, me, loan):
        super().__init__(me)
        self.loan = loan

    def perform(self):
        # for safety measure: once again truncate the amount to not exceed
        # the value of the loan
        amount = min(self.get_amount(), self.loan.get_value())
        self.loan.liabilityParty.get_ledger().subtract_cash(amount)
        self.loan.reduce_principal(amount)

    def get_max(self):
        return self.loan.get_value()


# 1. This is the generic Contract shared by all the 3 contracts definition
#    used in this model.
# 2. The 2 key functions are `get_action` and `is_eligible`. The latter
#    being used to filter whether the contract will be acted upon by an
#    agent.
# 3. For modularity purpose, actions are separated from the contracts
#    definition. So that they can be swapped with other types of action
#    whenever necessary.
class Contract:
    # ctype is defined to group very similar contracts together,
    # e.g. Loan and BailinableLoan are different classes but both have the same
    # ctype 'Loan'.
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


class AssetType:
    CORPORATE_BONDS = 1
    GOV_BONDS = 2


class Tradable(Contract):
    ctype = 'Tradable'

    def __init__(self, assetParty, assetType, assetMarket, quantity):
        super().__init__(assetParty, None)
        self.assetType = assetType
        self.assetMarket = assetMarket
        # `Tradable` has a price which may change over time.
        self.price = self.get_market_price()
        self.quantity = quantity
        # This is crucial to ensure order independence.
        # Amount being put for sale is added to this variable before
        # being cleared by AssetMarket in a separate turn.
        self.putForSale_ = 0.0

    def get_action(self, me):
        return SellAsset(self.assetParty, self)

    def is_eligible(self, me):
        return self.quantity > self.putForSale_

    def get_market_price(self):
        return self.assetMarket.get_price(self.assetType)

    def update_price(self):
        # Price has to be updated manually.
        self.price = self.get_market_price()

    def get_asset_type(self):
        return self.assetType

    def get_value(self):
        return self.quantity * self.price


# This is for illiquid contracts at either asset or liability side.
class Other(Contract):
    ctype = 'Other'

    def __init__(self, assetParty, liabilityParty, amount):
        super().__init__(assetParty, liabilityParty)
        self.principal = amount

    def get_value(self):
        return self.principal


# In general, loan is between banks or external nodes.
# In this model we are simplifying it to be just to external nodes.
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
