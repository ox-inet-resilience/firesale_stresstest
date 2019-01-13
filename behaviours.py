def do_nothing(bank):
    pass


def do_delever(bank):
    balance = bank.get_cash_()
    # 1. Pay off liabilities to delever
    deLever = min(balance, bank.leverageConstraint.get_amount_to_delever())
    if deLever > 0:
        deLever = bank.pay_off_liabilities(deLever)
        balance -= deLever

    # 2. Raise liquidity to delever later
    if balance < deLever:
        amount_to_raise = deLever - balance
        bank.sell_assets_proportionally(amount_to_raise)
