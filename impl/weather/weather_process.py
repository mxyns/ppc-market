import multiprocessing as mp
import os
import random
import math
from time import sleep


class WeatherInfo:

    def __init__(self, index, name, info_type="Dummy"):
        if not is_number(index) \
                or not isinstance(name, str) \
                or not isinstance(info_type, str):
            raise ValueError(f"wrong parameters given : \nindex={index}\nname={name}")

        self.index = index
        self.name = name
        self.type = info_type

    def eval(self, time):
        return None


class GaussianWeatherInfo(WeatherInfo):

    def __init__(self, name, mu, sigma, index=-1):
        super().__init__(index, name, "Gaussian")
        # TODO check for type
        self.mu = mu
        self.sigma = sigma

    def eval(self, time):
        return random.gauss(mu=self.mu, sigma=self.sigma)


class BEGWeatherInfo(WeatherInfo):
    def __init__(self, name, limit, tau, index=-1):
        super().__init__(index, name, "Bounded Exponential Growth")
        # TODO check for type
        self.limit = limit
        self.tau = tau

    def eval(self, time):
        return self.limit * (1 - math.exp(-time / self.tau))


class WeatherSource:

    def __init__(self, interval, shared_time, shared_data, infos, daemon=False):

        if not is_number(interval) \
                or not isinstance(shared_time, mp.sharedctypes.Synchronized) \
                or not isinstance(shared_data, mp.sharedctypes.SynchronizedArray) \
                or not isinstance(daemon, bool) \
                or False in [isinstance(el, WeatherInfo) for el in infos]:
            raise ValueError(f"wrong parameters given : \nindex={index}\nname={name}\ngenerator={generator}")

        self.interval = interval
        self.shared_time = shared_time
        self.shared_data = shared_data
        self.infos = infos
        for i, info in enumerate(infos) :
            info.index = i

        self.daemon = daemon

        self.process = None

    def deploy(self):

        self.process = mp.Process(target=self.run)

        # avoid zombie processes
        self.process.daemon = self.daemon
        self.process.name = "weather_source-" + str(random.randint(0, 10))
        return self.process

    def run(self):

        print(f"[{self.process.name} started. daemon={self.process.daemon}. pid={os.getpid()}. ppid={os.getppid()}]")

        time = -1
        while time >= -1:

            time = -1
            with self.shared_time.get_lock():
                time = self.shared_time.value

            if time >= 0:
                with self.shared_data.get_lock():
                    for i in range(len(self.infos)):
                        self.shared_data[i] = self.infos[i].eval(time)

            try:
                sleep(self.interval)
            except KeyboardInterrupt:
                exit(0)


def is_number(var):
    return type(var) in [float, int]
