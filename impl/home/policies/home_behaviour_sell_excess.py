import impl.home.home_comm_utils as comm_utils
from impl.home.home_comm_utils import cprint


def always_sell_excess_behaviour(owner, marketQ, homesQ):
    balance = owner.policy.current_balance()
    cprint(owner, f"{owner.id} => always_sell balance {balance}")

    if balance >= 0:
        cprint(owner, f"{owner.id} => i have a positive balance of {balance}, i'm done")
        return True, balance
    else:
        cprint(owner, f"{owner.id} => in need of {-balance} energy, requesting it")
        comm_utils.request_energy(owner=owner, queue=homesQ, amount=-balance)

    # if balance isnt positive we can still try to get energy from others
    return False, owner.policy.current_balance()
