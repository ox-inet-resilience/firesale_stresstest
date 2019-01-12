from collections import defaultdict
import numpy as np

from economicsl import Agent

from contracts import Tradable, Other, Loan, AssetType
from actions import PayLoan, SellAsset


class Order:
    def __init__(self, asset, quantity):
        self.asset = asset
        self.quantity = quantity

    def settle(self):
        self.asset.clear_sale(self.quantity)


class DefaultException(Exception):
    # In general, there are LIQUIDITY, SOLVENCY, FAILED_MARGIN_CALL
    # In this model, we are restricting it to SOLVENCY only.
    def __init__(self, me, typeOfDefault):
        self.typeOfDefault = typeOfDefault


class BankLeverageConstraint:
    def __init__(self, me):
        self.me = me

    def get_leverage(self):
        ldg = self.me.get_ledger()
        return ldg.get_equity_value() / ldg.get_asset_value()

    def is_insolvent(self):
        return self.get_leverage() < self.me.model.parameters.BANK_LEVERAGE_MIN

    def get_amount_to_delever(self):
        lev = self.get_leverage()
        is_below_buffer = lev < self.me.model.parameters.BANK_LEVERAGE_BUFFER
        if not is_below_buffer:
            return 0.0
        E = self.me.get_ledger().get_equity_value()
        current = E / lev
        target = E / self.me.model.parameters.BANK_LEVERAGE_TARGET
        return max(0, current - target)


class Bank(Agent):
    def __init__(self, name, simulation):
        super().__init__(name, simulation)
        self.availableActions = {}
        self.do_trigger_default = False
        self.leverageConstraint = BankLeverageConstraint(self)

    def init(self, model, assetMarket, assets, liabilities):
        cash, corp_bonds, gov_bonds, other_asset = assets
        loan, other_liability = liabilities
        self.model = model

        # Asset side
        self.add_cash(cash)
        cb_contract = Tradable(
            self, AssetType.CORPORATE_BONDS,
            assetMarket, corp_bonds)
        self.add(cb_contract)
        assetMarket.total_quantities[AssetType.CORPORATE_BONDS] += corp_bonds

        gb_contract = Tradable(
            self, AssetType.GOV_BONDS,
            assetMarket, gov_bonds)
        self.add(gb_contract)
        assetMarket.total_quantities[AssetType.GOV_BONDS] += gov_bonds

        self.add(Other(self, None, other_asset))

        # Liability side
        self.add(Loan(None, self, loan))
        self.add(Other(None, self, other_liability))

    def trigger_default(self):
        self.do_trigger_default = False

        self.sell_assets_proportionally()

    def is_insolvent(self):
        return self.leverageConstraint.is_insolvent()

    def get_available_actions(self):
        eligibleActions = defaultdict(list)
        ldg = self.get_ledger()
        for contract in (ldg.get_all_assets() + ldg.get_all_liabilities()):
            if contract.is_eligible(self):
                action = contract.get_action(self)
                eligibleActions[type(action)].append(action)

        return eligibleActions

    def choose_actions(self):
        # 0) If I'm insolvent, default.
        if self.is_insolvent():
            raise DefaultException(self, 'SOLVENCY')

        balance = self.get_cash_()
        # 1. Pay off liabilities to delever
        deLever = min(balance, self.leverageConstraint.get_amount_to_delever())
        if deLever > 0:
            deLever = self.pay_off_liabilities(deLever)
            balance -= deLever

        # 2. Raise liquidity to delever later
        if balance < deLever:
            amount_to_raise = deLever - balance
            self.sell_assets_proportionally(amount_to_raise)

    def step(self):
        if self.do_trigger_default:
            self.trigger_default()
        if self.alive:
            super().step()

    def act(self):
        if not self.alive:
            return
        self.availableActions = self.get_available_actions()
        try:
            self.choose_actions()
        except DefaultException:
            self.do_trigger_default = True
            self.alive = False
            self.simulation.bank_defaults_this_round += 1

    def pay_liability(self, amount, loan):
        amount = min(self.get_cash_(), amount)
        self.get_ledger().pay_liability(amount, loan)

    def pay_off_liabilities(self, amount):
        payLoanActions = self.get_all_actions_of_type(PayLoan)
        m = sum([a.get_max() for a in payLoanActions])
        if not (amount > 0):
                return 0.0

        for action in payLoanActions:
            action.set_amount(action.get_max() * amount / m)
            if action.get_amount() > 0:
                action.perform()
        return amount

    def set_initial_values(self):
        self.get_ledger().set_initial_values()

    def get_all_actions_of_type(self, actionType):
        return self.availableActions[actionType]

    def sell_assets_proportionally(self, amount=None):
        sellAssetActions = self.get_all_actions_of_type(SellAsset)
        totalSellableAssets = sum(a.get_max() for a in sellAssetActions)
        if amount is None:
            amount = totalSellableAssets
        if amount > 0:
            amount = min(totalSellableAssets, amount)

            for action in sellAssetActions:
                action.set_amount(
                    action.get_max() * amount / totalSellableAssets)
                action.perform()

            return amount
        else:
            return 0.0

    def update_asset_price(self, assetType):
        for asset in self.get_ledger().get_assets_of_type(Tradable):
            if asset.get_asset_type() == assetType:
                asset.update_price()


class AssetMarket:
    def __init__(self, model):
        self.model = model
        self.prices = defaultdict(lambda: 1.0)
        self.amountsSold = defaultdict(np.longdouble)
        self.totalAmountsSold = defaultdict(np.longdouble)
        self.orderbook = []
        self.oldPrices = {}
        self.total_quantities = defaultdict(np.longdouble)
        self.price_impacts = self.model.parameters.PRICE_IMPACTS

    def put_for_sale(self, asset, amount):
        assert amount > 0, amount
        self.orderbook.append(Order(asset, amount))
        atype = asset.get_asset_type()
        self.amountsSold[atype] += amount

    def clear_the_market(self):
        self.oldPrices = dict(self.prices)
        for atype, v in self.amountsSold.items():
            self.compute_price_impact(atype, v)

            newPrice = self.prices[atype]
            priceLost = self.oldPrices[atype] - newPrice
            if priceLost > 0:
                self.model.update_asset_price(atype)
            self.totalAmountsSold[atype] += v
        self.amountsSold = defaultdict(np.longdouble)

        for order in self.orderbook:
            order.settle()
        self.orderbook = []

    def compute_price_impact(self, assetType, amountSold):
        current_price = self.prices[assetType]
        price_impact = self.price_impacts[assetType]
        total = self.total_quantities[assetType]
        if total <= 0:
            return

        fraction_sold = amountSold / total

        # exponential price impact
        new_price = current_price * np.exp(-fraction_sold * price_impact)
        self.set_price(assetType, new_price)

    def get_price(self, assetType):
        return self.prices[assetType]

    def set_price(self, assetType, newPrice):
        self.prices[assetType] = newPrice
