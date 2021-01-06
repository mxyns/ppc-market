politics & economics : 

	import ...
	
	class ExternalEvent {

		constructor(
			name (string), 
			probability (double), 
			lifespan (int), 
			signal (signal.Signals : enum value), 
			handler (func)
			) {
			...
		}

		def happens() bool {

			return math.random() < this.probability
		}

		def up(pid) {
			this.signal(pid)
			this.ttl = this.lifespan
		}

		def down(pid) {
			this.signal(pid)
			this.ttl = -1
		}

		def signal(pid) {
			# send signal to process with PID = pid
			os.kill(pid, this.signal)
		}
	}

	class ExternalEventSource {

		constructor(name (string), events (list<ExternalEvent>), interval (int)) {
			...
		}

		def deploy() {

			# set handlers in parent process with calls deploy
			for (event in events) {
				signal.signal(event.signal, event.handler)
			}

			return (this.process = multiprocessing.Process(f=run, args=[interval, events]))
		}

		def run(interval (nonShared int), events (nonShared list)) {
			
			while True {

				# check if any event must occur and signal to parent if it needs to
				for (event in events) {
					if event.happens() {
						# send event's signal to parent process
						event.up(os.getppid())
						print(f"Event {event.name} fired signal {event.signal.name}")
					} else if event.ttl == 0 {
						# event just died, send death signal
						event.down() # after event.down() ttl < 0
					} else if event.ttl > 0 {
						# event wasn't triggered just now and is alive : reduce it's time to live
						event.ttl -= 1
					}
				}
	
				sleep(interval)
			}
		}
	}