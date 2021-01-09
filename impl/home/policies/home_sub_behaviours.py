import impl.home.home_comm_utils as comm_utils


def fulfill_some_request_sub_behaviour(owner, queue, block=False):
    print(f"{owner.id} -> tryna fulfill some requests")
    message, id = comm_utils.getSomeEnergyRequest(queue=queue, block=block)

    # check for energy requests
    if None not in (message, id):
        asked = float(message)
        sent = min(asked, owner.policy.current_balance())  # give the max we can without being in deficit
        print(f"{owner.id} => {id - 1} asked for {asked} energy, imma give u {sent} bro")
        if sent > 0:  # asked > 0 so if sent < 0 it means we are in deficit and we dont wanna get more debts
            owner.sendEnergy(queue=queue, destination=id - 1, count=sent)
    else:
        print(f"{owner.id} => aint no requests for me to fulfill imma keep my energy")
