import multiprocessing as mp
import os
import random
import math
from time import sleep


# a physical quantity to compute each tick. can be deterministic using time counter shared with market
class WeatherInfo:

    def __init__(self, index, name, unit="IS", info_type="Dummy"):
        if not is_number(index) \
                or not isinstance(name, str) \
                or not isinstance(info_type, str):
            raise ValueError(f"wrong parameters given : \nindex={index}\nname={name}")

        self.index = index          # where the value is placed in shared memory
        self.name = name            # name of the quantity, e.g. : temperature, humidity...
        self.type = info_type       # (unused) tells which type of function is used to compute the values (Gaussian, BEG, etc...)
        self.unit = unit            # the quantity's unit

    def eval(self, time):
        return None


# Weather Info following a gaussian probability generation
class GaussianWeatherInfo(WeatherInfo):

    def __init__(self, name, mu, sigma, unit="IS", index=-1):
        super().__init__(index=index, name=name, info_type="Gaussian", unit=unit)
        # TODO check for type
        self.mu = mu
        self.sigma = sigma

    def eval(self, time):
        return random.gauss(mu=self.mu, sigma=self.sigma)


# Weather Info following a bounded exponential growth : max_value * (1 - exp(-x/factor))
class BEGWeatherInfo(WeatherInfo):
    def __init__(self, name, limit, tau, unit="IS", index=-1):
        super().__init__(index=index, name=name, info_type="Bounded Exponential Growth", unit=unit)
        # TODO check for type
        self.limit = limit
        self.tau = tau

    def eval(self, time):
        return self.limit * (1 - math.exp(-time / self.tau))


# Weather Info Source, generates values for the infos and puts them in the shared memory
class WeatherSource:

    def __init__(self, interval, shared_time, shared_data, infos, daemon=False):

        if not is_number(interval) \
                or not isinstance(shared_time, mp.sharedctypes.Synchronized) \
                or not isinstance(shared_data, mp.sharedctypes.SynchronizedArray) \
                or not isinstance(daemon, bool) \
                or False in [isinstance(el, WeatherInfo) for el in infos]:
            raise ValueError(f"wrong parameters given")

        self.interval = interval            # tick duration
        self.shared_time = shared_time      # shared time counter with market
        self.shared_data = shared_data      # memory shared with market to put the data in
        self.infos = infos                  # list of WeatherInfo to generate
        for i, info in enumerate(infos) :   # automatically assigns an index based on the list's order
            info.index = i

        self.daemon = daemon                # is weather source daemon or not ?

        self.process = None                 # stored process object instance

    # deploys a process and returns it
    def deploy(self):

        self.process = mp.Process(target=self.run)

        # avoid zombie processes
        self.process.daemon = self.daemon
        self.process.name = "weather_source-" + str(random.randint(0, 10))
        return self.process

    # function ran by process
    def run(self):

        print(f"[{self.process.name}] started. daemon={self.process.daemon}. pid={os.getpid()}. ppid={os.getppid()}")

        time = -1
        while time >= -1: # wait for simulation to begin

            time = -1
            with self.shared_time.get_lock(): # safe access, potentially useless to acquire lock
                time = self.shared_time.value

            if time >= 0:
                with self.shared_data.get_lock(): # lock all of the array during the modification
                    for i in range(len(self.infos)): # generate values and put them in shared memory
                        self.shared_data[i] = self.infos[i].eval(time)

            try: # reduce annoying and useless errors in terminal on ctrl+c
                sleep(self.interval)
            except KeyboardInterrupt:
                exit(0)


def is_number(var):
    return type(var) in [float, int]
