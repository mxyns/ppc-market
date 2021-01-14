import multiprocessing
from multiprocessing.pool import ThreadPool
from random import random
from time import sleep

from sysv_ipc import MessageQueue

import impl.home.home_comm_utils as comm
import impl.politics_economics.politics_economics_process as events

events_presence = []


def main(interval,
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
         house_count=0
         ):
    multiprocessing.current_process().name = "market"

    P_last = P_init  # P = P_0

    market_queue = MessageQueue(key=market_queue_key)
    pool = ThreadPool(thread_pool_size)  # useless with last communication model

    # will store last weather info (non shared)
    weather = [None] * len(weather_source.infos)

    # deploy economics & politics
    economics = events.ExternalEventSource(name="economics", events=economics_events, interval=1000).deploy().start()
    politics = events.ExternalEventSource(name="politics", events=politics_events, interval=1000).deploy().start()

    if betas is None:
        betas = [random() - 0.5 for _ in range(len(weather_source.infos))]
        betas += [2 * random() + 1.2 for _ in range(len(economics_events) + len(politics_events))]

    weather_source.deploy().start()

    while True:
        print(f"[market] time is {shared_time.value}")

        print(f"[market] getting weather data...")
        # get weather info
        with weather_source.shared_data.get_lock():
            for info in weather_source.infos:
                weather[info.index] = weather_source.shared_data[info.index]

        print(f"[market] weather = {weather}")

        print(f"[market] waiting for houses")
        # use thread pool to get houses last values
        consumptions = pool.map(lambda tup: getHouseValue(tup[0], tup[1]),
                                [(market_queue, i) for i in range(house_count.value)])

        print(f"[market] consumptions = {consumptions}")

        # compute P_(t+1)
        last_price = P_last
        P_last = evalNewPrice(P_last, gamma, alphas, betas, weather, consumptions, events_presence)
        print(f"[market] price went from {last_price} to {P_last}")

        with shared_time.get_lock():
            shared_time.value += 1

        sleep(interval)


def getHouseValue(queue, house_id):
    print(f"[market] asking house {house_id} for consumption at mailbox {comm.market_request_id(house_id)}")
    comm.sendConsumptionRequest(queue=queue, id=house_id)
    return comm.awaitConsumptionResponse(queue=queue, id=house_id)


def evalNewPrice(P_last, gamma, alphas, betas, weather, homes_consumptions, events_presence):
    P_new = gamma * P_last  # compute P_t+1 value

    # alphas
    internal = [float(x[0]) for x in homes_consumptions]
    print(P_new, " += ", internal, " * ", alphas)
    for i in range(len(internal)):
        P_new += alphas[i] * internal[i]

    external = weather + events_presence
    print(P_new, " += ", external, " * ", betas)
    for i, factor in enumerate(external):
        P_new += betas[i] * factor

    return P_new


# toggle events_presence (f_i,t) coefficient (beta = 1 means the event is happening)
def toggleExternalFactor(name):
    events_presence[name] = 1 if events_presence[name] == 0 else 0


def make_event(name, prob, sig, lifespan, handler, args):
    events_presence.append(0)
    return events.ExternalEvent(name=name, probability=prob, sig=sig, lifespan=lifespan, handler=lambda: handler(*args))
