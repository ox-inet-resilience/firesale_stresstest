class BankLeverageConstraint:
    def __init__(self, me):
        self.me = me

    def get_leverage(self):
        # \lambda = E / A
        ldg = self.me.get_ledger()
        return ldg.get_equity_valuation() / ldg.get_asset_valuation()

    def is_insolvent(self):
        return self.get_leverage() < self.me.model.parameters.BANK_LEVERAGE_MIN

    def get_amount_to_delever(self):
        lev = self.get_leverage()
        # Banks act when \lambda < \lambda^{buffer}
        is_below_buffer = lev < self.me.model.parameters.BANK_LEVERAGE_BUFFER
        if not is_below_buffer:
            return 0.0
        E = self.me.get_ledger().get_equity_valuation()
        current = E / lev
        target = E / self.me.model.parameters.BANK_LEVERAGE_TARGET
        return max(0, current - target)
