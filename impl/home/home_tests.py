from home_process import *
import multiprocessing as mp
import math
import os
import sysv_ipc
from home_policy import getMessage, policies

def run_tests() :
	
	print("running home tests")

	homes_queue = sysv_ipc.MessageQueue(key=None, flags=sysv_ipc.IPC_CREX)
	market_queue = sysv_ipc.MessageQueue(key=None, flags=sysv_ipc.IPC_CREX)

	home_count = 2
	# homes = [Home((i, home_count), 100, 1000, policies[0]) for i in range(0, home_count)]
	homes = [ \
		Home((0, 3), 0.1, 1, policies[0]),\
		Home((1, 3), 0.1, 1, policies[1])\
	]

	deployer = HomeDeployer(100, homes_queue_key=homes_queue.key, market_queue_key=market_queue.key, homes=homes)
	deployer.deploy().start()
	deployer.process.join()

def queue_tests() :

	Q = sysv_ipc.MessageQueue(key=None, flags=sysv_ipc.IPC_CREX)
	print("1")
	a=getMessage(queue=Q, type_id=0, last=True)
	print(a)
	Q.send("mdr", type=1)
	print("2")
	a=getMessage(queue=Q, type_id=1, last=False)
	print(a)
	Q.send("ptdr", type=1)
	print("3")
	a=getMessage(queue=Q, type_id=0, last=False)
	print(a)
	Q.send("xptdr", type=1)
	Q.send("xptdr 2 ", type=1)
	Q.send("lol", type=2)
	print("4")
	a=getMessage(queue=Q, type_id=1, last=True)
	print(a)
	a=getMessage(queue=Q, type_id=2, last=False)
	print(a)
	print("should block")
	a=getMessage(queue=Q, type_id=2, last=False)
	print("passed ?!")