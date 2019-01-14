from collections import defaultdict

from economicsl import Agent

from contracts import Tradable, Other, Loan, AssetType
from constraints import BankLeverageConstraint
from behaviours import do_delever, sell_assets_proportionally


class DefaultException(Exception):
    # In general, there are LIQUIDITY, SOLVENCY, FAILED_MARGIN_CALL
    # In this model, we are restricting it to SOLVENCY only.
    def __init__(self, me, typeOfDefault):
        self.typeOfDefault = typeOfDefault


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
        # Register the contract amount to asset market. This is to be able to
        # compute the price impact, which is based on the total market
        # capitalisation, later.
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

    # trigger_default, is_insolvent, get_available_actions, choose_actions,
    # step, act, get_all_actions_of_type are standard functions of the
    # institutions in the full model.
    def trigger_default(self):
        self.do_trigger_default = False

        sell_assets_proportionally(self)

    def is_insolvent(self):
        # This has a particular implementation of just taking leverage ratio
        # into account. In general, this would include the solvency condition
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

        do_delever(self)

    def step(self):
        # In most agent-based models, there is only step().
        # We split it into step() and act() phases to ensure order independence
        # in some conditions. In the full model, trigger_default() may contain
        # a behavioural unit that does pull funding.
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
            # it performs bilateral pull funding in the full model), so
            # it is best to delay it to the step() stage.
            self.do_trigger_default = True
            self.alive = False
            # This is for record keeping.
            self.simulation.bank_defaults_this_round += 1

    def get_all_actions_of_type(self, actionType):
        return self.availableActions[actionType]

    def update_asset_price(self, assetType):
        # design choice: accounting is done by the institution itself,
        # not by the market.
        for asset in self.get_ledger().get_assets_of_type(Tradable):
            if asset.get_asset_type() == assetType:
                asset.update_price()
