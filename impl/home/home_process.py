from threading import Thread
import sysv_ipc
from time import sleep
import impl.home.home_comm_utils as comm_utils


class Home:

    def __init__(self, id_count_tuple, interval, slot_timeout, policy, market_queue_key=None, homes_queue_key=None):
        self.id = id_count_tuple[0]
        self.home_count = id_count_tuple[1]

        self.interval = interval
        self.slot_timeout = slot_timeout

        self.market_queue_key = market_queue_key
        self.homes_queue_key = homes_queue_key

        self.policy = policy

    def deploy(self):
        self.thread = Thread(target=self.run)
        return self.thread

    def run(self):
        print(f"hi from house #{self.id}")
        market_queue = sysv_ipc.MessageQueue(key=self.market_queue_key)
        homes_queue = sysv_ipc.MessageQueue(key=self.homes_queue_key)

        while True:
            # TODO          maybe migrate home from thread to process and multithread home so that
            # TODO-suite :  exchanges and communication are done in parallel

            # trading energy with homes until market asks us for an answer
            result = self.policy.execute(owner=self, comm=(market_queue, homes_queue))  # blocking op
            # result is how much the home wants to buy/sell, if result > 0 we sell or else we buy

            if result is None:  # just in case
                result = self.policy.last_decision

            # tell the market how much we want
            self.sendDecision(queue=market_queue, consumption=-result)  # blocking
            self.policy.reset()

            sleep(self.interval)

    def sendEnergy(self, queue, destination, count):

        print(f"It is I (home {self.id}) who sends {count}J to home {destination} at slot {comm_utils.energy_transfer_id(destination)}")
        comm_utils.sendEnergy(queue=queue, amount=count, destination=destination)
        self.policy.given += count

    def sendDecision(self, queue, consumption):
        sellbuy = "buys" if consumption > 0 else "sells"
        print(f"It is I (home {self.id}) who {sellbuy} {abs(consumption)}J to market")
        queue.send(message=str(consumption), type=comm_utils.MARKET_PURCHASE_REPLY_ID)


def is_number(var):
    return type(var) in [float, int]
