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
        if self.ttl < 0:
            self.alert()
        self.ttl = self.lifespan

    def down(self):
        self.alert()
        self.ttl = -1

    def alert(self):
        os.kill(os.getppid(), self.signal)


class ExternalEventSource:

    def __init__(self, name, events, interval, daemon=False):
        self.name = name
        self.events = events
        self.interval = interval
        self.process = None
        self.daemon = daemon

    def deploy(self):
        for event in self.events:
            signal.signal(event.signal, event.handler)
            event.handler = None

        self.process = multiprocessing.Process(target=self.run)
        self.process.daemon = self.daemon
        self.process.name = f"{self.name}-process"

        return self.process

    def run(self):

        print(f"[{self.process.name}] started. daemon={self.process.daemon}. pid={os.getpid()}. ppid={os.getppid()}]")
        print(f"[{self.process.name}] Events : ")
        for event in self.events:
            print(f"[{self.process.name}]    - {event.name} : p={event.probability} -> {event.signal}")

        while True:
            for event in self.events:
                if event.happens():
                    event.up()
                    print(f"[{self.process.name}]", "Event", event.name, "!")
                elif event.ttl == 0:
                    event.down()
                elif event.ttl > 0:
                    event.ttl -= 1
            try:
                time.sleep(self.interval)
            except KeyboardInterrupt:
                exit(0)
