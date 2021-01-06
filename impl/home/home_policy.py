import random
import time
import sysv_ipc

class Policy :

	def __init__(self, initial_cons, initial_prod, behaviour) :
		# TODO check types
		self.behaviour = behaviour
		self.last_decision = False
		self.consumption=initial_cons
		self.production=initial_prod
		self.reset()

	def reset(self) :
		self.given = 0
		self.received = 0

	def execute(self, owner, comm) :

		marketQ = comm[0]
		homesQ = comm[1]
	
		# timeout system
		decision = None
		market_msg = None
		start = time.time()
		while (time.time() - start) < owner.slot_timeout :
			if market_msg is None : # if market hasn't contacted us yet
				# check if we have a msg from market
				market_msg = getMessage(queue=marketQ, type_id=1, last=True) # TODO change type_id if we use a single Q for all market-home communication
				# if we've received a msg we record it's reception date
				if market_msg is None : start = time.time()

			# heuristic returns (done, value)
			decision = self.behaviour(owner, marketQ=marketQ, homesQ=homesQ)
			if decision[0] : 
				self.last_decision = decision[1]
				break

		# if we're done without being contacted by market we wait for it
		if market_msg is None : 
			print(f"home {owner.id} waiting")
			getMessage(queue=marketQ, type_id=1, last=False) # blocking

		return decision[1]

def always_sell_heuristic(owner, marketQ, homesQ) :
	return (True, owner.policy.production)

def always_give_heuristic(owner, marketQ, homesQ) : 

	# TODO communicate with homes
	message = getMessage(queue=homesQ, type_id=1, last=True) # non blocking bc we want the loop to keep checking for market messages
	# type 1 message are requests of format : sourceId|count
	if message is not None :
		message = message.split("|")
		asked = float(message[1])
		sent = min(asked, owner.policy.production - owner.policy.given) # give the max we can
		if sent > 0 :
			owner.policy.given += sent
			owner.sendEnergy(queue=homesQ, destination=int(message[0]), count=sent)

	# always False bc this one waits for the others => it's never done giving away
	# 0 because it will sell 0
	return (False, 0)

def sell_excess_heuristic(owner, marketQ, homesQ) : 
	pass

always_sell = Policy(100, 0, always_sell_heuristic)
always_give = Policy(100, 0, always_give_heuristic)
sell_excess = Policy(100, 0, sell_excess_heuristic)

policies=[always_sell, always_give, sell_excess]

def randomPolicy() :
	return policies[int(len(policies) * random.random())]

def getMessage(queue, type_id, last=False) :
	last_msg = None
	if not last :
		return queue.receive(block=True, type=type_id)
	else : 
		while True :
			try :
				tmp = queue.receive(block=False, type=type_id)
				last_msg = tmp
			except sysv_ipc.BusyError :
				return last_msg