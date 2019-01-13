from collections import defaultdict
import numpy as np

from economicsl import Agent

from contracts import Tradable, Other, Loan, AssetType
from actions import PayLoan, SellAsset, eps
from constraints import BankLeverageConstraint, DefaultException


class Bank(Agent):
    def __init__(self, name, simulation):
        super().__init__(name, simulation)
        # `availableActions` is a dictionary (aka hash map in other
        # languages) that has the action types (sell asset, pay loan)
        # as its keys and list of actions as its values.
        # It is reconstructed from scratch at every step.
        # E.g. {SellAsset: [sellasset1, sellasset2],
        #       PayLoan: [payloan1, payloan2, payloan3]}
        self.availableActions = {}
        self.do_trigger_default = False
        self.leverageConstraint = BankLeverageConstraint(self)

    def init(self, model, assetMarket, assets, liabilities):
        # init() is for initializing the balance sheet,
        # while __init__() is the standard Python method for
        # initializing an object
        cash, corp_bonds, gov_bonds, other_asset = assets
        loan, other_liability = liabilities
        self.model = model

        # Asset side
        self.add_cash(cash)
        # a1. Corporate bonds
        # Construct the contract
        cb_contract = Tradable(
            self, AssetType.CORPORATE_BONDS,
            assetMarket, corp_bonds)
        # Add the contract to balance sheet
        self.add(cb_contract)
        # Register the contract amount to asset market
        assetMarket.total_quantities[AssetType.CORPORATE_BONDS] += corp_bonds

        # a2. Goverment bonds
        gb_contract = Tradable(
            self, AssetType.GOV_BONDS,
            assetMarket, gov_bonds)
        self.add(gb_contract)
        assetMarket.total_quantities[AssetType.GOV_BONDS] += gov_bonds

        # a3. Other asset
        self.add(Other(self, None, other_asset))

        # Liability side
        # l1. Loan
        self.add(Loan(None, self, loan))
        # l2. Other liability
        self.add(Other(None, self, other_liability))

    def trigger_default(self):
        self.do_trigger_default = False

        self.sell_assets_proportionally()

    def is_insolvent(self):
        # In general, this would include the solvency condition
        # from risk-weighted capital ratio.
        return self.leverageConstraint.is_insolvent()

    def get_available_actions(self):
        # defaultdict is a convenient dictionary that
        # automatically creates an entry
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
            # In general, when a bank defaults, its default treatment
            # may be order-dependent if executed immediately (e.g. when
            # it performs bilateral pull funding in the full version of
            # the model), so it is best to delay it to the step()
            # stage.
            self.do_trigger_default = True
            self.alive = False
            # This is for record keeping.
            self.simulation.bank_defaults_this_round += 1

    def perform_proportionally(self, actions, amount=None):
        # This is a common pattern shared by sell assets and
        # pay loan.
        maximum = sum(a.get_max() for a in actions)
        if amount is None:
            amount = maximum
        if (maximum <= 0) or (amount <= 0):
            return 0.0
        amount = min(amount, maximum)
        for action in actions:
            action.set_amount(action.get_max() * amount / maximum)
            if action.get_amount() > 0:
                action.perform()
        return amount

    def pay_off_liabilities(self, amount):
        payLoanActions = self.get_all_actions_of_type(PayLoan)
        return self.perform_proportionally(payLoanActions, amount)

    def sell_assets_proportionally(self, amount=None):
        sellAssetActions = self.get_all_actions_of_type(SellAsset)
        return self.perform_proportionally(sellAssetActions, amount)

    def get_all_actions_of_type(self, actionType):
        return self.availableActions[actionType]

    def update_asset_price(self, assetType):
        for asset in self.get_ledger().get_assets_of_type(Tradable):
            if asset.get_asset_type() == assetType:
                asset.update_price()


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

        # This is the amounts sold for each step
        self.amountsSold = defaultdict(np.longdouble)
        # This is the cumulative amounts sold for each tradable asset
        # type.
        self.totalAmountsSold = defaultdict(np.longdouble)
        # The total market cap of the system.
        self.total_quantities = defaultdict(np.longdouble)
        self.orderbook = []

    def put_for_sale(self, asset, amount):
        assert amount > 0, amount
        self.orderbook.append(Order(asset, amount))
        atype = asset.get_asset_type()
        self.amountsSold[atype] += amount

    def clear_the_market(self):
        self.oldPrices = dict(self.prices)
        # 1. Update price based on price impact
        for atype, v in self.amountsSold.items():
            self.compute_price_impact(atype, v)

            newPrice = self.prices[atype]
            priceLost = self.oldPrices[atype] - newPrice
            if priceLost > 0:
                self.model.update_asset_price(atype)
            self.totalAmountsSold[atype] += v
        self.amountsSold = defaultdict(np.longdouble)

        # 2. Perform the sale
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

        # See Greenwood 2012 for the choice of the price impact
        # function.
        # Exponential price impact. `beta` is chosen such that
        # when 10% of the market cap is sold, the price drops by
        # 10%.
        beta = -10 * np.log(1 - price_impact)
        new_price = current_price * np.exp(-fraction_sold * beta)
        self.set_price(assetType, new_price)

    def get_price(self, assetType):
        return self.prices[assetType]

    def set_price(self, assetType, newPrice):
        self.prices[assetType] = newPrice
