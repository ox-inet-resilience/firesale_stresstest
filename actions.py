from economicsl import Action
eps = 1e-9


class SellAsset(Action):
    def __init__(self, me, asset):
        super().__init__(me)
        self.asset = asset

    def perform(self):
        if self.asset.price <= eps:
            return
        quantityToSell = self.get_amount() / self.asset.price
        if abs(quantityToSell) <= eps:
            return
        self.asset.put_for_sale(quantityToSell)

    def get_max(self):
        available_qty = self.asset.quantity - self.asset.putForSale_
        return available_qty * self.asset.price


class PayLoan(Action):
    def __init__(self, me, loan):
        super().__init__(me)
        self.loan = loan

    def perform(self):
        self.loan.pay_loan(self.get_amount())

    def get_max(self):
        return self.loan.get_value()
