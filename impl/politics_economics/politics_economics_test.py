from politics_economics_process import *
import signal

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
        probability=1,
        lifespan=10,
        sig=signal.SIGUSR1,
        handler=lambda: fhandler("shortage")
    )

    wr = ExternalEvent(
        name="war",
        probability=1,
        lifespan=100,
        sig=signal.SIGUSR2,
        handler=lambda: fhandler("war")
    )

    tn = ExternalEvent(
        name="tension",
        probability=1,
        lifespan=5,
        sig=signal.SIGWINCH,
        handler=lambda: fhandler("tension")
    )

    listEventE.append(sh)
    listEventP.append(wr)
    listEventP.append(tn)

    eco =  ExternalEventSource (
        name="Economics",
        listEvent=listEventE,
        interval=100
    )

    plt=  ExternalEventSource (
        name="Politics",
        listEvent=listEventP,
        interval=100
    )

    eco.deploy().start()
    plt.deploy().start()

def fhandler(name):
    events[name] = not events[name]

if __name__ == "__main__":
    run_tests()
    while True:
        print(events)