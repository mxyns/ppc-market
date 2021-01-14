import random
import time
import impl.home.home_comm_utils as comm_utils
from enum import Enum

from impl.home.policies.home_behaviour_give_excess import always_give_behaviour
from impl.home.policies.home_behaviour_sell_excess import always_sell_excess_behaviour
from impl.home.policies.home_behaviour_sell_if_no_takers import sell_if_no_takers_behaviour
from impl.home.home_comm_utils import cprint



class Behaviours(Enum):
    ALWAYS_SELL_EXCESS = always_sell_excess_behaviour
    ALWAYS_GIVE = always_give_behaviour
    SELL_IF_NO_TAKERS = sell_if_no_takers_behaviour

    def random(self):
        # can't list Enum bc attributes are functions, idk why
        return random.choice(list([self.ALWAYS_GIVE, self.ALWAYS_SELL_EXCESS, self.SELL_IF_NO_TAKERS]))


def new_policy(behaviour, initial_cons=100, initial_prod=150):
    if behaviour is None:
        raise ValueError()
    else:
        return Policy(behaviour=behaviour, initial_prod=initial_prod, initial_cons=initial_cons)


def randomPolicy():
    return new_policy(behaviour=Behaviours.random(Behaviours))


class Policy:

    def __init__(self, initial_cons, initial_prod, behaviour):
        # TODO check types
        self.behaviour = behaviour
        self.last_decision = None
        self.consumption = initial_cons
        self.production = initial_prod
        self.given = 0
        self.received = 0
        self.has_pending_request = False

    def reset(self):
        self.given = 0
        self.received = 0

    def current_balance(self):
        return (self.production + self.received) - (self.consumption + self.given)

    def execute(self, owner, comm):

        marketQ = comm[0]
        homesQ = comm[1]

        # timeout system
        decision = None
        market_msg = None
        start = time.time()
        while (time.time() - start) < owner.slot_timeout:
            if market_msg is None:  # if market hasn't contacted us yet
                # check if we have a msg from market
                market_msg = comm_utils.get_last_message(queue=marketQ, type_id=comm_utils.market_request_id(owner.id))
                # we store the last time we checked and we didn't have a message, this reset the timeout
                if market_msg is None:
                    start = time.time()
                    cprint(owner,  f"{owner.id} -> still no msg... {market_msg}")
                else:
                    cprint(owner,  f"{owner.id} -> msg from market !!!! {market_msg} starting slot timeout")

            # accept energy transfers
            if owner.policy.has_pending_request:
                comm_utils.accept_energy_transfers_if_any(owner=owner, queue=homesQ)

            # heuristic/behaviour returns (done, value)
            decision = self.behaviour(owner, marketQ=marketQ, homesQ=homesQ)
            if decision[0]:  # if done
                self.last_decision = decision[1]
                cprint(owner,  f"{owner.id} => i'm done!")
                break

            # sleep the required interval or less to answer the market's request in time
            time_left = abs(owner.slot_timeout - (time.time() - start))
            time.sleep(owner.interval if owner.interval < time_left else time_left)

        cprint(owner,  f"{owner.id} -> bitch i'm out")
        # just in case
        if self.has_pending_request:
            comm_utils.cancel_request(owner=owner, queue=homesQ)  # protects ourselves from receiving new energy transfers
            comm_utils.accept_energy_transfers_if_any(owner=owner, queue=homesQ)

        # if we're done without being contacted by market we wait for it
        if market_msg is None:
            cprint(owner,  f"home {owner.id} waiting on mailbox {comm_utils.market_request_id(owner.id)}")
            market_msg = comm_utils.get_last_message(queue=marketQ, type_id=comm_utils.market_request_id(owner.id),
                                                     block=True)  # blocking
            cprint(owner,  f"{owner.id} -> market told me '{market_msg}'")

        return decision[1]
