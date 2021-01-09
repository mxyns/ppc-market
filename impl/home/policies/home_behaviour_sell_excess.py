import impl.home.home_comm_utils as comm_utils


def always_sell_excess_behaviour(owner, marketQ, homesQ):
    balance = owner.policy.current_balance()
    print(f"{owner.id} => always_sell balance {balance}")

    if balance >= 0:
        print(f"{owner.id} => i have a positive balance of {balance}, i'm done")
        return True, balance
    else:
        print(f"{owner.id} => in need of {-balance} energy, requesting it")
        comm_utils.requestEnergy(owner=owner, queue=homesQ, amount=-balance)

    # if balance isnt positive we can still try to get energy from others
    return False, owner.policy.current_balance()
