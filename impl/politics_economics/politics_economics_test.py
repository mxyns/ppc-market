from politics_economics_process import *
import signal
import time

#TODO : LifeSpan variable

events = dict()
events["shortage"] = False
events["war"] = False
events["tension"] = False

listEventP = []
listEventE = []

def run_tests():
    print("Running politics_economics tests")

    sh = ExternalEvent(
        name="shortage",
        probability=0.00005,
        lifespan=5,
        sig=signal.SIGUSR1,
        handler=lambda _,__: fhandler("shortage")
    )

    wr = ExternalEvent(
        name="war",
        probability=0.000005,
        lifespan=2,
        sig=signal.SIGUSR2,
        handler=lambda _,__: fhandler("war")
    )

    tn = ExternalEvent(
        name="tension",
        probability=0.00005,
        lifespan=4,
        sig=signal.SIGWINCH,
        handler=lambda _,__: fhandler("tension")
    )

    listEventE.append(sh)
    listEventP.append(wr)
    listEventP.append(tn)

    eco =  ExternalEventSource (
        name="Economics",
        listEvent=listEventE,
        interval=1
    )

    plt=  ExternalEventSource (
        name="Politics",
        listEvent=listEventP,
        interval=1
    )

    eco.deploy().start()
    plt.deploy().start()

def fhandler(name):
    events[name] = not events[name]

if __name__ == "__main__":
    run_tests()
    while True:
        print("Shortage = ", events.get("shortage"))
        print("War = ", events.get("war"))
        print("Tension = ", events.get("tension"))
        time.sleep(1)