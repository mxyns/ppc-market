import impl.home.home_comm_utils as comm_utils
from impl.home.home_comm_utils import cprint


# common parts of a behaviours

# tries to fulfill a someones request
def fulfill_some_request_sub_behaviour(owner, queue, block=False):
    cprint(owner, f"[{owner.id}][fulfill_requests] -> tryna fulfill some requests")
    message, id = comm_utils.get_some_energy_request(queue=queue, block=block)

    # check for energy requests
    if None not in (message, id):
        asked = float(message)
        sent = min(asked, owner.policy.current_balance())  # give the max we can without being in deficit
        cprint(owner, f"[{owner.id}][fulfill_requests] => {id - 1} asked for {asked} energy, imma give u {sent} bro")
        if sent > 0:  # asked > 0 so if sent < 0 it means we are in deficit and we dont wanna get more debts
            owner.send_energy(queue=queue, destination=comm_utils.inverse_energy_request_id(id), count=sent)
    else:
        # cprint(owner, f"[{owner.id}][fulfill_requests] => aint no requests for me to fulfill imma keep my energy")
        pass
