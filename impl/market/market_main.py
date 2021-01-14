import multiprocessing as mp
import signal
from random import random

import impl.market.market_process as market
from impl.home.home_deployer import HomeDeployer
from impl.market.market_process import make_event, toggle_external_factor
from impl.weather.weather_process import WeatherSource, BEGWeatherInfo, GaussianWeatherInfo


def deploy_program(homes_queue_key, market_home_key, max_market_turns):
    shared_time = mp.Value('i', -1)

    print(f"MARKET_KEY = {market_home_key}\nHOME_KEY = {homes_queue_key}")

    shared_house_count = mp.Value('i', 5)
    deployer = HomeDeployer(interval=1, homes_queue_key=homes_queue_key, market_queue_key=market_home_key,
                            home_count=shared_house_count, daemon=True)
    deployer.deploy().start()

    weather_info = [
        GaussianWeatherInfo(name="Humidity", unit="%", mu=20, sigma=5),
        BEGWeatherInfo(name="Temperature", unit="°C", limit=38, tau=50)
    ]
    weather_source = WeatherSource(interval=.05,
                                   shared_time=shared_time,
                                   shared_data=mp.Array('d', len(weather_info)),
                                   infos=weather_info)

    market.main(
        interval=.1,
        max_market_turns=max_market_turns,
        P_init=100,
        thread_pool_size=8,
        alphas=[random() + 1 for _ in range(deployer.home_count.value)],
        gamma=1.2,
        weather_source=weather_source,
        market_queue_key=market_home_key,
        shared_time=shared_time,
        economics_events=[
            make_event(name="shortage", prob=0.0001, sig=signal.SIGWINCH, lifespan=5, handler=toggle_external_factor,
                       args="shortage")
        ],
        politics_events=[
            make_event(name="war", prob=0.000001, sig=signal.SIGUSR1, lifespan=10, handler=toggle_external_factor,
                       args="war"),
            make_event(name="tensions", prob=0.0003, sig=signal.SIGUSR2, lifespan=3, handler=toggle_external_factor,
                       args="tensions")
        ],
        house_count=shared_house_count
    )

    deployer.process.join()
    weather_source.process.join()
