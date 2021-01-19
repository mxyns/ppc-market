import os

from impl.home.home_process import Home
from impl.home.policies.home_policy import random_policy
import multiprocessing as mp
from impl.home.home_process import is_number


# Process containing all of the homes Threads
# should be able to be ran multiple times simultaneously with the same market but haven't tested yet
class HomeDeployer:

    def __init__(self, interval=1000, slot_timeout=1.0, homes_queue_key=None, market_queue_key=None, shared_home_count=None, new_home_count=None,
                 daemon=False, homes=None):

        # TODO check type
        if not is_number(interval) \
                or not isinstance(daemon, bool):
            raise ValueError(f"wrong parameters given : \nindex={index}\nname={name}\ngenerator={generator}")

        self.interval = interval                    # default interval to give to homes if homes aren't given as a parameter
        self.slot_timeout = slot_timeout            # default # maximum time we allow ourselves to make the market wait after it send a request

        self.market_queue_key = market_queue_key    # key to give to homes
        self.homes_queue_key = homes_queue_key      # key to give to homes

        self.homes = homes                          # array of homes, if None we generate 'new_home_count' homes
        self.home_count = shared_home_count

        # give key or generate homes if no homes given
        if self.homes is not None:
            for home in self.homes:
                home.market_queue_key = market_queue_key
                home.homes_queue_key = homes_queue_key

        elif new_home_count is not None and new_home_count >= 0 :
            self.homes = [
                Home(id_count_tuple=(i, self.home_count),
                     interval=self.interval,
                     slot_timeout=self.slot_timeout,
                     policy=random_policy(),
                     homes_queue_key=self.homes_queue_key,
                     see_thoughts=False,
                     market_queue_key=self.market_queue_key) for i in range(0, new_home_count)]
        else:
            raise ValueError("wrong parameters for new_home_count / shared_home_count")

        # register new homes so that market knows it can communicate with them
        with self.home_count.get_lock():
            self.home_count.value += len(self.homes)

        self.daemon = daemon
        self.process = None

    # deploy process
    def deploy(self):

        self.process = mp.Process(target=self.run)

        # avoid zombie processes
        self.process.daemon = self.daemon
        self.process.name = "home_deployer-" + str(self.home_count.value)
        return self.process

    # ran by process
    def run(self):

        print(f"[{self.process.name} started. daemon={self.process.daemon}. pid={os.getpid()}. ppid={os.getppid()}]")

        print(f"[{self.process.name}] starting homes")
        for i, home in enumerate(self.homes): # deploy homes
            home.deploy().start()
            print(f"[{self.process.name}] started home #{i}")

        print(f"[{self.process.name}] waiting for homes")
        for home in self.homes:
            home.thread.join()
