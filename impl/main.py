import multiprocessing
import os
import signal
import sys

sys.path.append(os.path.join(os.path.dirname(sys.argv[0]), "../"))

import multiprocessing as mp
import impl.deploy_program as program
import sysv_ipc


# x TODO checker que tout marche bien
# ~ TODO checker qu'on a tout fait -> manque
# x TODO trouver une solution qui donne pas un prix nul
#   TODO ajouter des bails bonus peut etre
# ~ TODO reformat output
if __name__ == '__main__':

    homes_queue = sysv_ipc.MessageQueue(key=None, flags=sysv_ipc.IPC_CREX)
    market_queue = sysv_ipc.MessageQueue(key=None, flags=sysv_ipc.IPC_CREX)

    curr = multiprocessing.current_process()
    curr.name = "main"
    print(f"[{curr.name}] started. daemon={curr.daemon}. pid={os.getpid()}. ppid={os.getppid()}")

    processes_to_kill = multiprocessing.Array('i', 6)
    process = mp.Process(target=program.deploy_program,
                         args=(homes_queue.key, market_queue.key, 100, processes_to_kill))
    process.start()

    print(f"[{curr.name}] ran program in {process.pid}")

    while not input("").lower().__contains__("stop"):
        pass

    with processes_to_kill.get_lock():
        for pid in processes_to_kill:
            os.kill(pid, signal.SIGKILL)

    homes_queue.remove()
    market_queue.remove()
    # do something ?
