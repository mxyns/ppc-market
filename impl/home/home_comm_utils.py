import sysv_ipc

# Home queue
# python has no int limit so im putting one bc the sysv_ipc in coded in C which has int limits
# limit determination : classical signed int32 max value is -> (1 << 32)/2 - 1 <=> 1 << 31 - 1
#                       we can only use positive values (sysv_ipc limitation => negative ids have a special behaviour in message queues)
#                       only strictly positive values * bc 0 is reserved for << accept any id >>
#                       split the positive interval in half : [1; 1 << 30 - 1] & [1 << 30 + 1; 1 << 31 - 1]
#                       2nd interval begins at 1 << 30 + 1 so that the intervals have equals lengths -> (1<<30 - 1) - 1 + 1 = (1<<31 - 1) - 1<<30 + 1 - 1
#                       we'll use the first interval for energy requests and the second for energy transfers


MAX_ENERGY_REQUEST_ID = (1 << 30) - 1  # max id of a home


def energy_request_id(house_id):
    return min(1 + house_id, MAX_ENERGY_REQUEST_ID)


def inverse_energy_request_id(request_id):
    return max(1, request_id - 1)


MIN_ENERGY_TRANSFER_ID = (1 << 30) + 1


def energy_transfer_id(house_id):
    return max(MIN_ENERGY_TRANSFER_ID + house_id, MIN_ENERGY_TRANSFER_ID)


def inverse_energy_transfer_id(transfer_id):
    return max(1, transfer_id - MIN_ENERGY_TRANSFER_ID)


# Market queue
MAX_MARKET_PURCHASE_REQUEST_ID = (1 << 30) - 1


def market_request_id(house_id):
    return min(1 + house_id, MAX_ENERGY_REQUEST_ID)


def inverse_market_request_id(request_id):
    return max(1, request_id - 1)


MIN_MARKET_PURCHASE_REPLY_ID = (1 << 30) + 1


def market_transfer_id(house_id):
    return max(MIN_ENERGY_TRANSFER_ID + house_id, MIN_ENERGY_TRANSFER_ID)


def inverse_market_transfer_id(purchase_id):
    return max(1, purchase_id - MIN_MARKET_PURCHASE_REPLY_ID)


def get_last_message(queue, type_id, block=False):
    last_msg = None
    first = True
    while True:
        try:
            tmp = queue.receive(block=False, type=type_id)
            last_msg = tmp
            first = False
        except sysv_ipc.BusyError:
            if first and block:
                return queue.receive(block=True, type=type_id)
            else:
                return last_msg


def get_message(queue, type_id, block=False):
    msg = None
    try:
        msg = queue.receive(block=block, type=type_id)
    except sysv_ipc.BusyError:
        return None, None
    else:
        return msg


def request_energy(owner, queue, amount):
    cprint(owner,  f"[requestEnergy] {owner.id} tries to request {amount} energy")
    cprint(owner,  f"[requestEnergy] {owner.id} has {'a' if owner.policy.has_pending_request else 'no'} pending request")
    if owner.policy.has_pending_request:
        return

    queue.send(str(amount), type=energy_request_id(owner.id))
    owner.policy.has_pending_request = True
    cprint(owner,  
        f"[requestEnergy] {owner.id} sent a request and now has {'a' if owner.policy.has_pending_request else 'no'} pending request")


def retrieve_energy_transfers(owner, queue):
    messages = []

    cprint(owner,  f"{owner.id} => did anyone send me sum energy at {energy_transfer_id(owner.id)} ?")
    message, id = get_message(queue=queue, type_id=energy_transfer_id(owner.id), block=False)
    cprint(owner,  f"{owner.id} => read ({message, id})")
    while message is not None:
        messages.append((message, id))
        cprint(owner,  f"{owner.id} => yes the bois sent me {float(message)} energy yeehaaww")
        message, id = get_message(queue=queue, type_id=energy_transfer_id(owner.id), block=False)
    cprint(owner,  f"{owner.id} => no more transfers for me :(")
    return messages


def accept_energy_transfers_if_any(owner, queue):
    replies = retrieve_energy_transfers(owner, queue)
    for reply in replies:  # reply is (message(string of float), msg_id)
        amount = float(reply[0])
        owner.policy.received += amount
    owner.policy.has_pending_request &= not len(replies) > 0

    cprint(owner,  f"house {owner.id} accepted {len(replies)} transfers")


def cancel_request(owner, queue):
    # empties the message queues from all of the owner's requests
    get_last_message(queue=queue, type_id=energy_request_id(owner.id))
    cprint(owner,  f"house {owner.id} cancelled its energy request")


def get_some_energy_request(queue, max_to_give=None, block=False):
    message, id = get_message(queue=queue, type_id=-MAX_ENERGY_REQUEST_ID, block=block)  # get any energy request message
    if max_to_give is None or max_to_give >= float(message) >= 0:
        # <=> we dont have any max limit or max_to_give >= 0 && float(message) <= max_to_give
        return message, id
    else:  # we cant fulfill this request, so we put it back where it belongs
        queue.send(message=message, type=id, block=block)

    return None, None


def send_energy(queue, amount, destination):
    queue.send(message=str(amount), type=energy_transfer_id(destination))


def send_consumption_request(queue, id):
    # TODO give weather info to houses
    queue.send(message=f"how much house {id} pls?", type=market_request_id(id))


def await_consumption_response(queue, id):
    msg, id = queue.receive(type=market_transfer_id(id), block=True)
    return (msg, inverse_market_transfer_id(id))


def cprint(home, *args):
    if home.see_thoughts :
        cprint(owner,  *args, file=home.out)
