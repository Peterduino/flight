#######################################################################################
# Xeon rocket ignition script, manages processes and scripts for the shared variables #
#######################################################################################

from multiprocessing import Process, Manager
import time
from dataReader import data_reader
from secu import secu
from pilot import pilot

from gpsReader import gps_reader

if __name__ == '__main__':

    manager = Manager()
    shared_data = manager.dict()

    p1 = Process(target=data_reader, args=(shared_data,))
    p2 = Process(target=gps_reader, args=(shared_data,))
    p3 = Process(target=secu, args=(shared_data,))
    p4 = Process(target=pilot, args=(shared_data,))


    scripts = [p1, p2, p3, p4]

    for script in scripts:
        script.start()

    time.sleep(1003)          # EARTHSHAKING SETTING : time before the rocket unactivates AFTER TAKE OFF, in secounds (e.g. 5min = 300)
    print("MAIN: stop")

    for script in scripts:
        script.terminate()

    for script in scripts:
        script.join()
