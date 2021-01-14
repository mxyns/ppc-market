from impl.home.home_process import Home
from impl.home.policies.home_policy import randomPolicy
import multiprocessing as mp
from impl.home.home_process import is_number


class HomeDeployer:

    def __init__(self, interval=1000, slot_timeout=1.0, homes_queue_key=None, market_queue_key=None, home_count=3,
                 daemon=True, homes=None):

        # TODO check type
        if not is_number(interval) \
                or not isinstance(daemon, bool):
            raise ValueError(f"wrong parameters given : \nindex={index}\nname={name}\ngenerator={generator}")

        self.interval = interval
        self.slot_timeout = slot_timeout

        self.market_queue_key = market_queue_key
        self.homes_queue_key = homes_queue_key

        self.homes = homes
        if self.homes is None:
            self.home_count = home_count
        else:
            self.home_count = mp.Value('i', len(homes))
            for home in homes:
                home.market_queue_key = market_queue_key
                home.homes_queue_key = homes_queue_key

        self.daemon = daemon
        self.process = None

    def deploy(self):

        self.process = mp.Process(target=self.run)

        # avoid zombie processes
        self.process.daemon = self.daemon
        self.process.name = "home_deployer-" + str(self.home_count.value)
        return self.process

    def run(self):

        if self.homes is None:
            self.homes = [
                Home((i, self.home_count), self.interval, self.slot_timeout, randomPolicy(), self.homes_queue_key,
                     self.market_queue_key) for i in range(0, self.home_count.value)]

        time = -1

        print("starting homes")
        for i, home in enumerate(self.homes):
            home.deploy().start()
            print(f"started home #{i}")

        print("waiting for homes")
        for home in self.homes:
            home.thread.join()
