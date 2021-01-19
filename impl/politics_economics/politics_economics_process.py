import multiprocessing
import signal
import os
import time
import random


# an event that uses signals to communicate to parent process
class ExternalEvent:

    def __init__(self, name, probability, lifespan, sig, handler):
        self.name = name                    # event name
        self.probability = probability      # probability of happening each tick
        self.lifespan = lifespan            # how much ticks an event lasts
        self.ttl = -1                       # time to live <=> how much time before death
        self.signal = sig                   # associated signal
        self.handler = handler              # handler function

    # returns true if the event occured
    def happens(self):
        return random.random() < self.probability

    # signal parent (market) that event is on if it was dead.
    # just reset it ttl if already alive and signaled.
    def up(self):
        if self.ttl < 0:
            self.alert()
        self.ttl = self.lifespan

    # signals death to parent (market)
    def down(self):
        self.alert()
        self.ttl = -1

    # sends signal to parent (market)
    def alert(self):
        os.kill(os.getppid(), self.signal)


# a source of events (ExternalEvent)
class ExternalEventSource:

    def __init__(self, name, events, interval, daemon=False):
        self.name = name            # name of the source (used to identify source in terminal)
        self.events = events        # list of events to fire randomly
        self.interval = interval    # tick duration
        self.process = None         # stored process object instance
        self.daemon = daemon        # if process should be daemon or not

    # deploys a process, assigns handlers and returns process.
    # should be ran in parent for handlers to work properly
    def deploy(self):
        for event in self.events:
            signal.signal(event.signal, event.handler)
            event.handler = None

        self.process = multiprocessing.Process(target=self.run)
        self.process.daemon = self.daemon
        self.process.name = f"{self.name}-process"

        return self.process

    # function executed by the process
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
                elif event.ttl == 0:    # last tick of life. kill event and signal parent
                    event.down()
                elif event.ttl > 0:     # still alive, decrease ttl
                    event.ttl -= 1
            try:
                time.sleep(self.interval)
            except KeyboardInterrupt:
                exit(0)
