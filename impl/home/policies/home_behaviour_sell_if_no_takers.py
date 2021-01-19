from impl.home.policies.home_sub_behaviours import fulfill_some_request_sub_behaviour
import impl.home.home_comm_utils as comm_utils
from impl.home.home_comm_utils import cprint


# self explanatory
def sell_if_no_takers_behaviour(owner, marketQ, homesQ):
    balance = owner.policy.current_balance()

    if balance == 0:
        cprint(owner, f"[{owner.id}][no_takers->sell] => i have exactly 0 energy left, i'm done")
        return True, balance
    elif balance > 0:  # if we have a surplus of energy we sell it
        cprint(owner, f"[{owner.id}][no_takers->sell] => i have {balance} excess, i'm tryna give sum")
        fulfill_some_request_sub_behaviour(owner, homesQ, block=False)
    else:  # when in need of energy
        cprint(owner, f"[{owner.id}][no_takers->sell] => im thirsty for energy, gimme {-balance} pls")
        comm_utils.request_energy(owner=owner, queue=homesQ, amount=-balance)  # -balance bc balance < 0

    return False, owner.policy.current_balance()
