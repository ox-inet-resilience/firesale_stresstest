from economicsl import Action
eps = 1e-9


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
        # put for sale
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
        amount = min(self.get_amount(), self.loan.get_value())
        self.loan.liabilityParty.pay_liability(amount, self.loan)
        self.loan.liabilityParty.get_ledger().subtract_cash(amount)
        self.loan.reduce_principal(amount)

    def get_max(self):
        return self.loan.get_value()
