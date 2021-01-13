import sys
import os
sys.path.append(os.path.join(os.path.dirname(sys.argv[0]), "../../"))

from impl.home.home_tests import *

if __name__ == "__main__":

    # TODO close properly MessageQueues
    print("running home temporary parent")

    run_tests()
    queue_tests()
