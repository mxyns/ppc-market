import multiprocessing as mp
import signal
from random import random

import impl.market.market_process as market
from impl.home.home_deployer import HomeDeployer
from impl.home.home_process import Home
from impl.market.market_process import make_event, toggle_external_factor
from impl.weather.weather_process import WeatherSource, BEGWeatherInfo, GaussianWeatherInfo


def deploy_program(homes_queue_key, market_queue_key, max_market_turns, to_kill):
    shared_time = mp.Value('i', -1)

    print(f"MARKET_KEY = {market_queue_key}\nHOME_KEY = {homes_queue_key}")

    shared_house_count = mp.Value('i', 0)
    deployer = HomeDeployer(interval=.1, homes_queue_key=homes_queue_key, market_queue_key=market_queue_key,
                            shared_home_count=shared_house_count, daemon=True, homes=[
            Home(id_count_tuple=(0, shared_house_count),  # mecs sympas avec des panneaux solaires
                 interval=0.2,
                 slot_timeout=1.0,
                 policy=new_policy(behaviour=Behaviours.ALWAYS_GIVE, initial_prod=300, initial_cons=50),
                 homes_queue_key=homes_queue_key,
                 see_thoughts=False,
                 market_queue_key=market_queue_key),
            Home(id_count_tuple=(1, shared_house_count),  # mecs sympas mais qui veulent de l'argent qd mm
                 interval=0.2,
                 slot_timeout=1.0,
                 policy=new_policy(behaviour=Behaviours.SELL_IF_NO_TAKERS, initial_prod=150, initial_cons=60),
                 homes_queue_key=homes_queue_key,
                 see_thoughts=False,
                 market_queue_key=market_queue_key),
            Home(id_count_tuple=(2, shared_house_count),  # c'est ma maison je consomme normalement
                 slot_timeout=1.0,
                 interval=0.2,
                 policy=new_policy(behaviour=Behaviours.ALWAYS_SELL_EXCESS, initial_prod=20, initial_cons=60),
                 homes_queue_key=homes_queue_key,
                 see_thoughts=False,
                 market_queue_key=market_queue_key),
            Home(id_count_tuple=(3, shared_house_count),  # c'est ma maison je consomme normalement
                 slot_timeout=1.0,
                 interval=0.2,
                 policy=new_policy(behaviour=Behaviours.ALWAYS_SELL_EXCESS, initial_prod=20, initial_cons=60),
                 homes_queue_key=homes_queue_key,
                 see_thoughts=False,
                 market_queue_key=market_queue_key),
            Home(id_count_tuple=(4, shared_house_count),  # Je suis une baie de brassage je ne fais que consommer
                 slot_timeout=1.0,
                 interval=.2,
                 policy=new_policy(behaviour=Behaviours.ALWAYS_SELL_EXCESS, initial_prod=10, initial_cons=30),
                 homes_queue_key=homes_queue_key,
                 see_thoughts=False,
                 market_queue_key=market_queue_key)
        ])
    deployer.deploy().start()
    with to_kill.get_lock():
        to_kill[0] = deployer.process.pid

    weather_info = [
        GaussianWeatherInfo(name="Humidity", unit="%", mu=20, sigma=5),
        BEGWeatherInfo(name="Temperature", unit="°C", limit=38, tau=50)
    ]
    weather_source = WeatherSource(interval=.05,
                                   shared_time=shared_time,
                                   shared_data=mp.Array('d', len(weather_info)),
                                   infos=weather_info, daemon=True)
    weather_source.deploy().start()
    with to_kill.get_lock():
        to_kill[1] = weather_source.process.pid

    market_args = dict(
        interval=2,
        max_market_turns=max_market_turns,
        P_init=100,
        thread_pool_size=8,
        alphas=[random() + 1 for _ in range(deployer.home_count.value)],
        gamma=1.2,
        weather_source=weather_source,
        market_queue_key=market_queue_key,
        shared_time=shared_time,
        economics_events=[
            make_event(name="shortage", prob=0.001, sig=signal.SIGPIPE, lifespan=10, handler=toggle_external_factor,
                       args=("shortage", 3))
        ],
        politics_events=[
            make_event(name="war", prob=0.00001, sig=signal.SIGUSR1, lifespan=10, handler=toggle_external_factor,
                       args=("war", 1.3)),
            make_event(name="tensions", prob=0.003, sig=signal.SIGUSR2, lifespan=3, handler=toggle_external_factor,
                       args=("tensions", 1.2))
        ],
        house_count=shared_house_count
    )
    market_process = mp.Process(target=market.main, kwargs=market_args, daemon=False)  # bc has children
    market_process.start()
    with to_kill.get_lock():
        to_kill[2] = market_process.pid

    market_process.join()
    weather_source.process.join()
    deployer.process.join()
