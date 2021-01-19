import impl.home.home_comm_utils as comm_utils
from impl.home.home_comm_utils import cprint


# self explanatory
def always_sell_excess_behaviour(owner, marketQ, homesQ):
    balance = owner.policy.current_balance()

    if balance >= 0:
        cprint(owner, f"[{owner.id}][always_sell] => i have a positive balance of {balance}, imma sell")
        return True, balance
    else:
        cprint(owner, f"[{owner.id}][always_sell] => in need of {-balance} energy, requesting it")
        comm_utils.request_energy(owner=owner, queue=homesQ, amount=-balance)

    # if balance isnt positive we can still try to get energy from others
    return False, owner.policy.current_balance()
