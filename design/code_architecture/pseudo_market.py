market :

	from ... import ExternalEvent, ExternalEventSource 
	from multiprocessing.pool import ThreadPool
	import signal

	def main(interval (nonShared int), 
		shared_time (multiprocessing.Value<int>), 
		shared_weather_data (multiprocessing.Array<double>), 
		shared_houses_queues (multiprocessing.Array<multiprocessing.Queue>),
		thread_pool_size (float),
		alphas (nonShared list<float>),
		betas (nonShared list<float>),
		gamma (float),
		P_init (float)
		) {

		P_last = P_init # P = P_0

		pool = ThreadPool(thread_pool_size) # useless with last communication model

		# will store last weather info (non shared)
		weather = dict()
		events_presence = []

		# deploy economics & politics
		(new ExternalEventSource("economics", [
			ExternalEvent("shortage", 0.0001, signal.SIGQUIT, () => toggleExternalFactor(betas, 0))
			], 1000)).deploy().start()

		(new ExternalEventSource("politics", [
			ExternalEvent("war", 0.000001, signal.SIGUSR1, () => toggleExternalFactor(betas, 1))
			ExternalEvent("tensions", 0.0003, signal.SIGUSR2, () => toggleExternalFactor(betas, 2))
			], 1000)).deploy().start()

		while True {

			# use thread pool to get houses last values
			consumptions = pool.map(getHouseValue, shared_houses_queues)
			
			# get weather info
			with shared_weather_data.get_lock() {
				weather["temperature"] = shared_weather_data[0] # not atomic ?
				weather["humidity"] = shared_weather_data[1] # not atomic ?
				weather["raining"] = shared_weather_data[2] # not atomic ?
			}

			# wait for all houses responses
			pool.join()

			# compute P_(t+1)
			P_last = evalNewPrice(P_last, gamma, alphas, betas, weather, consumptions, events_presence)
			
			with shared_time.get_lock() {
				shared_time.value += 1
			}

			sleep(interval)
		}
	}

	def evalNewPrice(P_last, gamma, alphas, betas, weather, homes_consumptions, events_presence) {
		... # compute P_t+1 value
		return P_new
	}

	# toggle events_presence (f_i,t) coefficient (beta = 1 means the event is happening)
	def toggleExternalFactor(events_presence, integer) {

		curr = events_presence[integer]
		if events_presence[integer] == 0 {
			events_presence[integer] = 1
		} else {
			events_presence[integer] = 0
		}
	}