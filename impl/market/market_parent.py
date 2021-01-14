import sys
import os

sys.path.append(os.path.join(os.path.dirname(sys.argv[0]), "../../"))

import multiprocessing as mp
import signal
from random import random
import sysv_ipc

import impl.market.market_process as market
from impl.home.home_deployer import HomeDeployer
from impl.market.market_process import make_event, toggleExternalFactor
from impl.weather.weather_process import WeatherSource, BEGWeatherInfo, GaussianWeatherInfo

if __name__ == "__main__":
    shared_time = mp.Value('i', -1)

    homes_queue = sysv_ipc.MessageQueue(key=None, flags=sysv_ipc.IPC_CREX)
    market_queue = sysv_ipc.MessageQueue(key=None, flags=sysv_ipc.IPC_CREX)

    print(f"MARKET_KEY = {market_queue.key}\nHOME_KEY = {homes_queue.key}")

    shared_house_count = mp.Value('i', 2)
    deployer = HomeDeployer(.01, homes_queue_key=homes_queue.key, market_queue_key=market_queue.key, home_count=shared_house_count)
    deployer.deploy().start()

    weather_info = [
        GaussianWeatherInfo(name="Humidity", mu=20, sigma=5),
        BEGWeatherInfo(name="Temperature", limit=38, tau=50)
    ]
    weather_source = WeatherSource(interval=.05,
                                   shared_time=shared_time,
                                   shared_data=mp.Array('d', len(weather_info)),
                                   infos=weather_info)

    market.main(
        interval=.1,
        P_init=100,
        thread_pool_size=8,
        betas=[random() - 0.5 for _ in range(len(weather_info))]
              + [random()],
        alphas=[random() + 1 for _ in range(deployer.home_count.value)],
        gamma=1.2,
        weather_source=weather_source,
        market_queue_key=market_queue.key,
        shared_time=shared_time,
        economics_events=[
            make_event(name="shortage", prob=0.0001, sig=signal.SIGWINCH, lifespan=5, handler=toggleExternalFactor,
                       args="shortage")
        ],
        politics_events=[
            make_event(name="war", prob=0.000001, sig=signal.SIGUSR1, lifespan=10, handler=toggleExternalFactor,
                       args="war"),
            make_event(name="tensions", prob=0.0003, sig=signal.SIGUSR2, lifespan=3, handler=toggleExternalFactor,
                       args="tensions")
        ],
        house_count=shared_house_count
    )

    deployer.process.join()
    weather_source.process.join()
