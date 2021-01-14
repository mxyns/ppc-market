import multiprocessing
import signal
import os
import time
import random


class ExternalEvent:

    def __init__(self, name, probability, lifespan, sig, handler):
        self.name = name
        self.probability = probability
        self.lifespan = lifespan
        self.ttl = -1
        self.signal = sig
        self.handler = handler
        
    def happens(self):
        return random.random() < self.probability

    def up(self):
        self.alert()
        self.ttl = self.lifespan

    def down(self):
        self.alert()
        self.ttl = -1

    def alert(self):
        os.kill(os.getppid(), self.signal)


class ExternalEventSource:

    def __init__(self, name, events, interval):
        self.name = name
        self.events = events
        self.interval = interval
        self.process = None

    def deploy(self):
        for event in self.events:
            signal.signal(event.signal, event.handler)
            event.handler = None

        self.process = multiprocessing.Process(target=self.run)
        self.process.name = f"{self.name}-process"

        return self.process

    def run(self):
        while True:
            for event in self.events:
                if event.happens():
                    event.up()
                    print("Event ", event.name, " fired signal ", event.signal.name, "")
                elif event.ttl == 0:
                    event.down()
                elif event.ttl > 0:
                    event.ttl -= 1
            time.sleep(self.interval)