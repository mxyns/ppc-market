from impl.home.policies.home_sub_behaviours import fulfill_some_request_sub_behaviour
import impl.home.home_comm_utils as comm_utils


def sell_if_no_takers_behaviour(owner, marketQ, homesQ):
    balance = owner.policy.current_balance()

    print(f"{owner.id} => sell if no takers balance {balance}")

    if balance == 0:
        print(f"{owner.id} => i have exactly 0 energy left, i don't need to sell or buy, i'm good")
        return True, balance
    elif balance > 0:  # if we have a surplus of energy we sell it
        print(f"{owner.id} => i have too much energy, i'm tryna give u sum")
        fulfill_some_request_sub_behaviour(owner, homesQ, block=False)
    else:  # when in need of energy
        print(f"{owner.id} => im thirsty for energy, gimme {-balance} pls")
        comm_utils.requestEnergy(owner=owner, queue=homesQ, amount=-balance)  # -balance bc balance < 0

    return False, owner.policy.current_balance()
