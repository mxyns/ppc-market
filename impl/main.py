import multiprocessing
import sys
import os

sys.path.append(os.path.join(os.path.dirname(sys.argv[0]), "../"))

import multiprocessing as mp
import impl.market.market_main as program
import sysv_ipc


if __name__ == '__main__':

    homes_queue = sysv_ipc.MessageQueue(key=None, flags=sysv_ipc.IPC_CREX)
    market_queue = sysv_ipc.MessageQueue(key=None, flags=sysv_ipc.IPC_CREX)

    curr = multiprocessing.current_process()
    curr.name = "main"
    print(f"[{curr.name} started. daemon={curr.daemon}. pid={os.getpid()}. ppid={os.getppid()}]")

    process = mp.Process(target=program.deploy_program, args=(homes_queue.key, market_queue.key, 100), daemon=False)
    process.start()

    # do something ?

    print()

