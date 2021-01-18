import multiprocessing
import os
from multiprocessing.pool import ThreadPool
from random import random
from time import sleep

from sysv_ipc import MessageQueue

import impl.home.home_comm_utils as comm
import impl.politics_economics.politics_economics_process as events

events_presence = dict()


def main(interval,
         max_market_turns=100,
         P_init=100,
         thread_pool_size=12,
         betas=None,
         alphas=(),
         gamma=1.0,
         weather_source=None,
         market_queue_key=-1,
         shared_time=None,
         economics_events=(),
         politics_events=(),
         house_count=None
         ):
    process = multiprocessing.current_process()
    process.name = "market"

    print(f"[{process.name} started. daemon={process.daemon}. pid={os.getpid()}. ppid={os.getppid()}]")

    current_price = P_init  # P = P_0

    market_queue = MessageQueue(key=market_queue_key)

    # will store last weather info (non shared)
    weather = [None] * len(weather_source.infos)

    # deploy economics & politics
    events.ExternalEventSource(name="economics", events=economics_events, interval=.5, daemon=True).deploy().start()
    events.ExternalEventSource(name="politics", events=politics_events, interval=.5, daemon=True).deploy().start()

    if betas is None:
        betas = [random() + 1 for _ in range(len(weather_source.infos))]
        betas += [2 * random() + 1.2 for _ in range(len(economics_events) + len(politics_events))]

    with ThreadPool(thread_pool_size) as pool:
        turns = 0
        while turns <= max_market_turns:
            print(f"\n=====================\n")
            print(f"[{process.name}] Time is {shared_time.value}TU")

            # get weather info
            print(f"[{process.name}] Weather :")
            with weather_source.shared_data.get_lock():
                for info in weather_source.infos:
                    weather[info.index] = weather_source.shared_data[info.index]
                    print(f"[{process.name}]    - {info.name}   :   {weather[info.index]} {info.unit}")

            if sum(list(events_presence.values())) > 0:
                print(f"[{process.name}] Ongoing events :")
                for event in events_presence:
                    if events_presence[event] > 0:
                        print(f"[{process.name}]    - {event} -> x{events_presence[event]}")

            # use thread pool to get houses last values
            try:
                consumptions = pool.map(lambda tup: get_house_consumption(tup[0], tup[1]),
                                        [(market_queue, i) for i in range(house_count.value)])
            except:
                pool.close()
                print(f"[{process.name}] error while getting houses values. aborting")
                exit(0)

            print(f"\n[{process.name}] Houses [{house_count.value}] :")
            for i, cons in enumerate(consumptions):
                print(
                    f"[{process.name}]    - House {i} :   {- float(cons[0])}EU  {- current_price * float(cons[0])}MU")  # EU = Energy Unit, MU = Money Unit

            # compute P_(t+1)
            last_price = current_price
            current_price = compute_new_price(current_price, gamma, alphas, betas, weather, consumptions,
                                              events_presence)
            print(f"\n[{process.name}] Price went from {last_price}MU to {current_price}MU")

            with shared_time.get_lock():
                shared_time.value += 1

            turns += 1
            sleep(interval)

            print(f"\n=====================\n")


def get_house_consumption(queue, house_id):
    # print(f"[{process.name}] asking house {house_id} for consumption at mailbox {comm.market_request_id(house_id)}")
    comm.send_consumption_request(queue=queue, id=house_id)
    return comm.await_consumption_response(queue=queue, id=house_id)


def compute_new_price(P_last, gamma, alphas, betas, weather, homes_consumptions, events_presence):
    P_new = gamma * P_last  # compute P_t+1 value

    # alphas
    internal = [float(x[0]) for x in homes_consumptions]
    print(f"[{multiprocessing.current_process().name}]", P_new, " += ", internal, " * ", alphas)
    for i in range(len(internal)):
        P_new += alphas[i] * internal[i]

    external = weather + list(events_presence.values())
    print(f"[{multiprocessing.current_process().name}]", P_new, " += ", external, " * ", betas)
    for i, factor in enumerate(external):
        P_new += betas[i] * factor

    return max(0, P_new)


# toggle events_presence (f_i,t) coefficient (beta = 1 means the event is happening)
def toggle_external_factor(name, factor):
    events_presence[name] = factor if events_presence[name] == 0 else 0


def make_event(name, prob, sig, lifespan, handler, args):
    events_presence[name] = 0
    event = events.ExternalEvent(name=name, probability=prob, sig=sig, lifespan=lifespan,
                                 handler=lambda _, __: handler(*args))
    return event
