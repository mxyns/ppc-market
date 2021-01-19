import json
from threading import Thread
import sysv_ipc
from time import sleep
import impl.home.home_comm_utils as comm_utils
from impl.home.home_comm_utils import cprint


# object representing a home and wrapping a home thread
class Home:

    def __init__(self, id_count_tuple, interval, slot_timeout, policy, market_queue_key=None, homes_queue_key=None,
                 see_thoughts=False, out="/ppc/houses/"):
        self.id = id_count_tuple[0]  # home id, used to determine messages types in message queues
        self.home_count = id_count_tuple[1]  # (unused) shared home count

        self.interval = interval  # interval between action batches
        self.slot_timeout = slot_timeout  # maximum time we allow ourselves to make the market wait after it send a request

        self.market_queue_key = market_queue_key  # key to market-home message queue
        self.homes_queue_key = homes_queue_key  # key to home-home message queue

        self.policy = policy  # policy taking decisions for the home
        self.thread = None  # the home's thread object instance

        self.see_thoughts = see_thoughts  # True if the home should print its thought process in the terminal

    # deploys a thread
    def deploy(self):
        self.thread = Thread(target=self.run)
        self.thread.name = "home-" + str(self.id)
        return self.thread

    # ran by the thread
    def run(self):
        cprint(self, f"[{self.id}] hi from house #{self.id}")

        # open needed queues
        market_queue = sysv_ipc.MessageQueue(key=self.market_queue_key)
        homes_queue = sysv_ipc.MessageQueue(key=self.homes_queue_key)

        last_market_infos = None
        while True:
            # TODO          maybe migrate home from thread to process and multithread home so that
            # TODO-bis      exchanges and communication are done in parallel

            self.special_weather_things(infos=last_market_infos) # special actions to take in regards to current market state

            # trading energy with homes until market asks us for an decision
            result, infos = self.policy.execute(owner=self, comm=(market_queue, homes_queue)) # blocking op
            # result is how much the home wants to buy/sell, if result > 0 we sell or else we buy

            if result is None:  # just in case
                result = self.policy.last_decision
            if infos is not None:
                try:
                    last_market_infos = json.loads(infos)
                except Exception:
                    pass

            # tell the market how much we want
            self.send_decision(queue=market_queue, consumption=-result)  # blocking # take opposite of decision bc for market negative consumption is selling
            self.policy.reset() # reset production / consumption / given energy / received energy state for next tick

            sleep(self.interval)

    # send energy to an another home
    def send_energy(self, queue, destination, count):

        cprint(self,
               f"[{self.id}] It is I (home {self.id}) who sends {count}J to home {destination} at slot {comm_utils.energy_transfer_id(destination)}")
        comm_utils.send_energy(queue=queue, amount=count, destination=destination)
        self.policy.given += count

    # send decision to market
    def send_decision(self, queue, consumption):
        sellbuy = "buys" if consumption > 0 else "sells"
        cprint(self, f"[{self.id}] It is I (home {self.id}) who {sellbuy} {abs(consumption)}J to market")
        queue.send(message=str(consumption), type=comm_utils.market_transfer_id(self.id))

    # special actions to take in regards to current market state
    def special_weather_things(self, infos):
        if infos is None:
            return

        print(f"[{self.id}] {infos}")
        if infos["Temperature"] < 0:
            cprint(self,
                   f"[{self.id}] Temperature => consumption : {self.policy.consumption} -> {self.policy.consumption * 2}")
            self.policy.consumption *= 2


def is_number(var):
    return type(var) in [float, int]
