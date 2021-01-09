from impl.home.policies.home_sub_behaviours import fulfill_some_request_sub_behaviour
import impl.home.home_comm_utils as comm_utils


def always_give_behaviour(owner, marketQ, homesQ):
    balance = owner.policy.current_balance()

    print(f"{owner.id} => always give balance {balance}")

    if balance == 0:
        print(f"{owner.id} => i have exactly 0 energy left, i cant' give anymore, i'm done")
        return True, balance
    elif balance > 0:
        # non blocking bc we want the loop to keep checking for market messages
        # check if there is a request
        print(f"{owner.id} => i wanna give sum energy to ma bois")
        fulfill_some_request_sub_behaviour(owner, homesQ, block=False)
    else:
        comm_utils.requestEnergy(owner=owner, queue=homesQ, amount=-balance)
    # FIXME TODO : idk if always give should also request energy to keep itself above 0, we must ask teachers about that
    # NB this can't happen unless the home has this strategy and has initial_cons > initial_prod bc when we have i_prod > i_cons we give just enough to fall back to 0 energy

    # always False bc this one waits for the others => it's never done giving away
    # min between 0 and current balance bc if balance is > 0 we dont sell and keep in case we can give
    # if balance is < 0 we're in deficit and need to buy from market
    return False, min(0, owner.policy.current_balance())
