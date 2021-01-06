from threading import Thread
import multiprocessing as mp
import sysv_ipc
from home_policy import *
from time import sleep

class HomeDeployer : 

	def __init__(self, interval=1000, slot_timeout=1.0, homes_queue_key=None, market_queue_key=None, home_count=3, daemon=True, homes=None) :

		# TODO check type
		if not is_number(interval) \
		or not isinstance(daemon, bool) :
			raise ValueError(f"wrong parameters given : \nindex={index}\nname={name}\ngenerator={generator}")

		self.interval = interval
		self.slot_timeout = slot_timeout

		self.market_queue_key = market_queue_key
		self.homes_queue_key = homes_queue_key

		self.homes = homes
		if self.homes is None :
			self.home_count = 3
		else :
			self.home_count = len(homes)
			for home in homes : 
				home.market_queue_key = market_queue_key
				home.homes_queue_key = homes_queue_key

		self.daemon = daemon
		self.process = None

	def deploy(self) :

		self.process = mp.Process(target=self.run)

		# avoid zombie processes
		self.process.daemon = self.daemon
		return self.process

	def run(self) :

		if self.homes is None :
			self.homes = [Home((i, self.home_count), self.interval, self.slot_timeout, randomPolicy(), self.homes_queue_key, self.market_queue_key) for i in range(0, self.home_count)]

		time = -1

		print("starting homes")
		for i, home in enumerate(self.homes) :
			home.deploy().start()
			print(f"started home #{i}")

		print("waiting for homes")
		for home in self.homes :
			home.thread.join()

class Home :

	def __init__(self, id_count_tuple, interval, slot_timeout, policy, market_queue_key=None, homes_queue_key=None) :
		
		self.id = id_count_tuple[0]
		self.home_count = id_count_tuple[1]

		self.interval = interval
		self.slot_timeout = slot_timeout

		self.market_queue_key = market_queue_key
		self.homes_queue_key = homes_queue_key

		self.policy = policy


	def deploy(self) :
		
		self.thread = Thread(target=self.run)
		return self.thread


	def run(self) :

		print(f"hi from house #{self.id}")
		market_queue = sysv_ipc.MessageQueue(key=self.market_queue_key)
		homes_queue = sysv_ipc.MessageQueue(key=self.homes_queue_key)

		while True :
				
			# TODO maybe migrate home from thread to process and multithread home so that 
			# exchanges and communication are done in parallel
			self.policy.execute(owner=self, comm=(market_queue, homes_queue)) # blocking op : energy negociation with homes

			self.sendDecision(queue=market_queue,consumption=self.policy.last_decision) # blocking
			self.policy.reset()

			sleep(self.interval)

	def sendEnergy(self, queue, destination, count) :
		print(f"It I (home {self.id}) who sends {count}J to home {destination}")
		queue.send(message=str(count), type=2 + destination)

	def sendDecision(self, queue, consumption) :
		print(f"It I (home {self.id}) who buys {consumption}J to market")
		queue.send(message=str(consumption), type=2)


def is_number(var) :
	return type(var) in [float, int]