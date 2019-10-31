from contracts import PayLoan, SellAsset

# List of strategies that consists of behavioural units

def do_nothing(bank):
    pass


def do_delever(bank):
    balance = bank.get_cash_()
    # 1. Pay off liabilities to delever
    amountToDeLever = bank.leverageConstraint.get_amount_to_delever()
    if amountToDeLever > 0:
        deLever = pay_off_liabilities(bank, min(amountToDeLever, balance))
        balance -= deLever
        amountToDeLever -= deLever

    # 2. Raise liquidity to delever later
    if balance < amountToDeLever:
        amount_to_raise = amountToDeLever - balance
        sell_assets_proportionally(bank, amount_to_raise)

# List of behavioural units
def perform_proportionally(bank, actions, amount=None):
    # This is a common pattern shared by sell assets and
    # pay loan.
    # See Greenwood 2015 and Cont-Schaanning 2017.
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

def pay_off_liabilities(bank, amount):
    payLoanActions = bank.get_all_actions_of_type(PayLoan)
    return perform_proportionally(bank, payLoanActions, amount)

def sell_assets_proportionally(bank, amount=None):
    sellAssetActions = bank.get_all_actions_of_type(SellAsset)
    return perform_proportionally(bank, sellAssetActions, amount)
