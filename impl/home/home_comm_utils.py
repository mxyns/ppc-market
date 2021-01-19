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

# makes the id corresponding to an energy request from a house id
def energy_request_id(house_id):
    return min(1 + house_id, MAX_ENERGY_REQUEST_ID)

# makes a house id from the corresponding energy request id
def inverse_energy_request_id(request_id):
    return max(1, request_id - 1)


MIN_ENERGY_TRANSFER_ID = (1 << 30) + 1


# makes the id corresponding to an energy transfer (gift/mailbox) from a house id
def energy_transfer_id(house_id):
    return max(MIN_ENERGY_TRANSFER_ID + house_id, MIN_ENERGY_TRANSFER_ID)


# makes a house id from the corresponding energy transfer (gift/mailbox)
def inverse_energy_transfer_id(transfer_id):
    return max(1, transfer_id - MIN_ENERGY_TRANSFER_ID)


# Market queue
MAX_MARKET_PURCHASE_REQUEST_ID = (1 << 30) - 1


# makes the id corresponding to a market request to a house id
def market_request_id(house_id):
    return min(1 + house_id, MAX_ENERGY_REQUEST_ID)

# makes a house id from the corresponding market request to a house
def inverse_market_request_id(request_id):
    return max(1, request_id - 1)


MIN_MARKET_PURCHASE_REPLY_ID = (1 << 30) + 1


# makes the id corresponding to a market answer from a house
def market_transfer_id(house_id):
    return max(MIN_ENERGY_TRANSFER_ID + house_id, MIN_ENERGY_TRANSFER_ID)


# makes a house id from the corresponding market answer from a house source id
def inverse_market_transfer_id(purchase_id):
    return max(1, purchase_id - MIN_MARKET_PURCHASE_REPLY_ID)


# gets last message in a message queue
# if block=False we just return the last
# if block=True we wait for the next message after clearing the queue and return it on reception
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


# get a message from a queue, handling BusyErrors
def get_message(queue, type_id, block=False):
    msg = None
    try:
        msg = queue.receive(block=block, type=type_id)
    except sysv_ipc.BusyError:
        return None, None
    else:
        return msg


# request a certain amount of energy to other houses
def request_energy(owner, queue, amount):
    if owner.policy.has_pending_request:
        return

    queue.send(str(amount), type=energy_request_id(owner.id))
    owner.policy.has_pending_request = True
    cprint(owner, f"[{owner.id}][requestEnergy] sent a request and now has {'a' if owner.policy.has_pending_request else 'no'} pending request")


# get all energy gifts gotten from others houses
def retrieve_energy_transfers(owner, queue):
    messages = []

    # cprint(owner,  f"[{owner.id}] => did anyone send me sum energy at {energy_transfer_id(owner.id)} ?")
    message, id = get_message(queue=queue, type_id=energy_transfer_id(owner.id), block=False)
    # cprint(owner,  f"{owner.id} => read ({message, id})")
    while message is not None:
        messages.append((message, id))
        cprint(owner,  f"[{owner.id}] => yes the bois sent me {float(message)} energy yeehaaww")
        message, id = get_message(queue=queue, type_id=energy_transfer_id(owner.id), block=False)
    # cprint(owner,  f"{owner.id} => no more transfers for me :(")
    return messages


# gets gifts and adds it to received gifts register
def accept_energy_transfers_if_any(owner, queue):
    replies = retrieve_energy_transfers(owner, queue)
    for reply in replies:  # reply is (message(string of float), msg_id)
        amount = float(reply[0])
        owner.policy.received += amount
    owner.policy.has_pending_request &= not len(replies) > 0

    cprint(owner,  f"[{owner.id}] accepted {len(replies)} transfers")


# cancels an energy request
def cancel_request(owner, queue):
    # empties the message queues from all of the owner's requests
    get_last_message(queue=queue, type_id=energy_request_id(owner.id))
    cprint(owner,  f"[{owner.id}] cancelled its unfulfilled energy request")


# tries to get a fulfillable request (according to needs given in parameters)
# puts back request in its queue if the needs aren't met
def get_some_energy_request(queue, max_to_give=None, block=False):
    message, id = get_message(queue=queue, type_id=-MAX_ENERGY_REQUEST_ID, block=block)  # get any energy request message
    if max_to_give is None or max_to_give >= float(message) >= 0:
        # <=> we dont have any max limit or max_to_give >= 0 && float(message) <= max_to_give
        return message, id
    else:  # we cant fulfill this request, so we put it back where it belongs
        queue.send(message=message, type=id, block=block)

    return None, None


# send energy to a house
def send_energy(queue, amount, destination):
    queue.send(message=str(amount), type=energy_transfer_id(destination))


# used by market to ask homes for consumption report
def send_consumption_request(queue, id, message=f"how much house {id} pls?"):
    queue.send(message=message, type=market_request_id(id))


# used by market to await the consumption report
def await_consumption_response(queue, id):
    msg, id = queue.receive(type=market_transfer_id(id), block=True)
    return msg, inverse_market_transfer_id(id)


# conditional print (prints if home.see_thoughts is True)
def cprint(home, *args):
    if home.see_thoughts :
        print(*args)
