import sysv_ipc
from impl.home.home_deployer import HomeDeployer

from impl.home.home_comm_utils import getMessage
from impl.home.home_process import *
from impl.home.policies.home_policy import Behaviours, new_policy


def run_tests():
    print("running home tests")

    homes_queue = sysv_ipc.MessageQueue(key=None, flags=sysv_ipc.IPC_CREX)
    market_queue = sysv_ipc.MessageQueue(key=None, flags=sysv_ipc.IPC_CREX)

    print(f"MARKET_KEY = {market_queue.key}\nHOME_KEY = {homes_queue.key}")

    home_count = 2
    # homes = [Home((i, home_count), 100, 1000, policies[0]) for i in range(0, home_count)]
    homes = [
        Home(id_count_tuple=(0, 3), interval=5, slot_timeout=10, policy=new_policy(behaviour=Behaviours.ALWAYS_GIVE, initial_cons=50, initial_prod=150)),
    ]

    deployer = HomeDeployer(100, homes_queue_key=homes_queue.key, market_queue_key=market_queue.key, homes=homes)
    deployer.deploy().start()
    deployer.process.join()


def queue_tests():
    Q = sysv_ipc.MessageQueue(key=None, flags=sysv_ipc.IPC_CREX)
    print("1")
    a = getMessage(queue=Q, type_id=0, block=True)
    print(a)
    Q.send("mdr", type=1)
    print("2")
    a = getMessage(queue=Q, type_id=1, block=False)
    print(a)
    Q.send("ptdr", type=1)
    print("3")
    a = getMessage(queue=Q, type_id=0, block=False)
    print(a)
    Q.send("xptdr", type=1)
    Q.send("xptdr 2 ", type=1)
    Q.send("lol", type=2)
    print("4")
    a = getMessage(queue=Q, type_id=1, block=True)
    print(a)
    a = getMessage(queue=Q, type_id=2, block=False)
    print(a)
    print("should block")
    a = getMessage(queue=Q, type_id=2, block=False)
    print("passed ?!")
