home : 
	import ...
	
	class Policy {

		constructor(initial_cons (float), initial_prod (float), heuristic (func (me, comm_queue) => float)) {
			...
			this.last_decision = false
		}

		def compute(me, queue_to_others) {
			return (this.last_decision = this.heuristic(me, queue_to_others))
		}
	}


	first_policy = Policy(100, 0, ...)
	second_policy = Policy(100, 0, ...)
	last_policy = Policy(100, 0, ...)

	def randomPolicy(p1, p2) {
		rnd = math.random()
		if rnd <= p1 {
			return first_policy
		} else if rnd <= p2 {
			return second_policy
		} else {
			return last_policy
		}
	}

	class Home(Thread) {

		constructor(
			(id, home_count) (int, int), 
			interval (int),
			policy (Policy), 
			market_queue (sys_ipc.MessageQueue),
			homes_queue (list<sys_ipc.MessageQueue>)) {
			...
		}

		def deploy() {
			return (this.thread = threading.Thread(f=this.run, args=(this.id, this.interval, this.policy, this.market_queue_key, this.homes_queue_key)))
		}

		def run(id, interval, policy, market, homes) {

			market_queue = sysv_ipc.MessageQueue(key=market)
			homes_queue = sysv_ipc.MessageQueue(key=homes)

			while true {
				
				# maybe id specific
				getLastMessage(queue=market_queue, type=1, block=true) # await from consumption request
				
				sendDecision(queue=market_queue, consumption=policy.compute(this, homes_queue), type=2) # blocking

				sleep(interval)
			}
		}
	}

	def main(home_count, market_queue_key, homes_queue_key) {

		houses = []
		for (i in range(home_count)) {
			houses[i] = new Home(i, home_update_interval, home.randomPolicy(0.33, 0.33), market_to_home_queue_key, interhouse_communications_queue_key)
			houses[i].deploy().start()
		}

		# TODO 
		# get houses responses, sum values, send to market

		for (i in range(home_count)) {
			houses[i].join()
		}
	}

	def sendDecision(queue, decision, type) {
		queue.send(message=decision, type=type)
	}

	def getLastMessage(queue, type, block) {
		last = null
		while true {
			try {
				tmp = queue.receive(block=block, type=type)
				last = tmp
			} except BusyError {
				return last
			}
		}
	}