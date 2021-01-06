weather : 

	import ...

	class WeatherInfo {

		constructor(index (int), name (string), generator (func)) {
			...
		}

		def eval(time) {
			this.generator(time)
		}
	}

	class WeatherSource {

		constructor(
			interval (nonShared int), 
			shared_time (multiprocessing.Value<int>), 
			shared_data (multiprocessing.Array<double>), 
			infos (list<WeatherInfo>)
			) {
			...
		}

		def deploy() {

			return (this.process = multiprocessing.Process(f=this.run, args=[this.interval, this.shared_time, this.shared_data, this.infos]))
		}

		def run(interval, shared_time, shared_data, infos) {

			while True {

				time = -1
	
				with shared_time.get_lock() {
					time = shared_time.value
				}
				# time = shared_time.value # atomic ? 
	
				# simulation has begun
				if time >= 0 {
					# compute each weather value and store it in shared memory
					# lock whole block so that market doesn't compute P_t while we are updating values
					with shared_data.get_lock() {
						for (info in infos) {
							shared_data.get_obj().set(info.eval(time))
						}
					}
				}
	
				sleep(interval)
			}
		}
	}