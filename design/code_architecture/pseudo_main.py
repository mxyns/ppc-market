main :
	
	import ...

	# TODO :
	# 	interhouse communication
	# 	market to house communication (why would i need a multithreaded environment ?)

	# program entry point, argsl is map of : launch parameter => value
	main(argsl) {

		# HQ (old name)
		market_to_home_queue = new sysv_ipc.MessageQueue()
		market_to_home_queue_key = market_to_home_queue.key

		print(f"market_to_home_queue_key={market_to_home_queue_key}")

		# setup homes
		home_count = argsl["home_count"]
		home_update_interval = argsl["home_interval"]
		houses = []

		# Q
		interhouse_communications_queue = new sysv_ipc.MessageQueue()
		interhouse_communications_queue_key = interhouse_communications_queues.key

		# TODO : MQ

		print(f"interhouse_communications_queue_key={interhouse_communications_queue_key}")

		home_count = argsl["home_count"]
		home_process = multiprocessing.Process(f=home.main, args=[
				home_count,
				market_queue_key,
				homes_queue_key
			])

		shared_time = multiprocessing.Value('i', -1)
		shared_weather_data = multiprocessing.Array('d', 2)
		weather_update_interval = argsl["weather_interval"]


		# deploy a weather source
		list<WeatherInfo> weather_infos = []
		weather_infos.append(WeatherInfo(0, "temperature", t => 20 + simplex_noise(t)))
		weather_infos.append(WeatherInfo(1, "humidity", t => 30 + simplex_noise(t)))
		weather_infos.append(WeatherInfo(2, "raining", t => math.random() < 0.01))

		weather_source = WeatherSource(weather_update_interval, shared_time, shared_weather_data, weather_infos)
		weather_process = weather_source.deploy()
		weather_process.start()

		market_update_interval = argsl["market_interval"]
		market_thread_pool_size = argsl["market_pool_size"]
		market_gamma = argsl["market_gamma"]
		market_initial_price = argsl["market_p0"]

		market_process = multiprocessing.Process(f=market.main, args=[
				market_update_interval,
				shared_time,
				shared_weather_data,
				market_to_homes_queue, # FIXME synchronized array of queues ? for what ? no use i think
				market_thread_pool_size,
				alphas=[........................],
				betas=[.....................],
				market_gamma,
				market_initial_price,
			]).start()

		home_process.start()

		weather_process.join()
		market_process.join()
		home_process.join()

		market_to_homes_queue.close()
		interhouse_communications_queue.close()
	}