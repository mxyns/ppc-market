from weather_process import *
import multiprocessing as mp
import math
import os
from time import sleep

def run_tests() :
	print(f"{os.getpid()} running weather tests")
	
	wi = BEGWeatherInfo("imameasurand", 100, 10)

	print([wi.eval(i) for i in range(0,20)])

	measurands = [wi] + [GaussianWeatherInfo(f"rng-event-{i}", i*i, i) for i in range(1,5)]
	

	shared_time = mp.Value('i', -1)
	shared_data = mp.Array('d', len(measurands))
	ws = WeatherSource(           
		interval=1,
		shared_time=shared_time,
		shared_data=shared_data,
		infos=measurands
		)

	ws.deploy().start()

	# generate some values
	generations = 15
	time = 0
	while time < generations : 
		with shared_data.get_lock() :
			for i in range(len(measurands)) :
				print(f"{measurands[i].name}[{measurands[i].type}] = {shared_data[i]}")
				# print(f"{measurands[i].name} = {shared_data[i]}")
		
		with shared_time.get_lock() :
			shared_time.value = (time := time + 1)

		sleep(1)


	# indirectly kill weather source
	with shared_time.get_lock() :
		shared_time.value = -2
	
	ws.process.join()
	print("exited")