import multiprocessing
from multiprocessing.pool import ThreadPool
from time import sleep

from sysv_ipc import MessageQueue

import impl.home.home_comm_utils as comm
import impl.politics_economics.politics_economics_process as events

events_presence = []


def main(interval,
         P_init,
         thread_pool_size,
         betas,
         alphas,
         gamma,
         weather_source,
         market_queue_key,
         shared_time,
         economics_events,
         politics_events,
         house_count
         ):

    multiprocessing.current_process().name = "market"

    P_last = P_init  # P = P_0

    market_queue = MessageQueue(key=market_queue_key)
    pool = ThreadPool(thread_pool_size)  # useless with last communication model

    # will store last weather info (non shared)
    weather = []

    # deploy economics & politics
    economics = events.ExternalEventSource(name="economics", events=economics_events, interval=1000).deploy().start()
    politics = events.ExternalEventSource(name="politics", events=politics_events, interval=1000).deploy().start()

    weather_source.deploy().start()

    while True:
        # use thread pool to get houses last values
        consumptions = pool.map(lambda tup: getHouseValue(tup[0], tup[1]), [(market_queue, i) for i in range(house_count.value)])

        # get weather info
        with weather_source.shared_data.get_lock():
            for info in weather_source.infos:
                weather[info.index] = weather_source.shared_data[info.index]

        # wait for all houses responses
        pool.join()

        # compute P_(t+1)
        P_last = evalNewPrice(P_last, gamma, alphas, betas, weather, consumptions, events_presence)

        with shared_time.get_lock():
            shared_time.value += 1

        sleep(interval)


def getHouseValue(queue, house_id):
    comm.sendConsumptionRequest(queue=queue, id=house_id)
    return comm.awaitConsumptionResponse(queue=queue, id=house_id)


def evalNewPrice(P_last, gamma, alphas, betas, weather, homes_consumptions, events_presence):
    P_new = gamma * P_last  # compute P_t+1 value

    # alphas
    internal = [x[0] for x in homes_consumptions]
    for i in range(len(internal)):
        P_new += alphas[i] * internal[i]

    external = weather + events_presence
    for i, factor in enumerate(external):
        P_new += betas[i] * factor

    return P_new


# toggle events_presence (f_i,t) coefficient (beta = 1 means the event is happening)
def toggleExternalFactor(name):
    events_presence[name] = 1 if events_presence[name] == 0 else 0


def make_event(name, prob, sig, lifespan, handler, args):
    events_presence.append(0)
    return events.ExternalEvent(name=name, probability=prob, sig=sig, lifespan=lifespan, handler=lambda: handler(*args))
