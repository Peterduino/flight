import time
import serial
from serial.serialutil import SerialException
from util_calculations import latOf, longOf, listNMEA, testNMEA, datasGPS, set_update_rate

def gps_reader(shared_data):

    uart = serial.Serial("/dev/ttyS0", baudrate=9600, timeout=10)

    dataTxt = open("./datas/datasGPS.txt", "a")
    dataTxt.write('\n\n\n\n ===================================================================\n')

    coordTxt = open( "./datas/datasCoord.txt","a")
    coordTxt.write('\n\n\n\n ===================================================================\n')

    set_update_rate(uart,100)

    start = time.monotonic()

    while True:

        timeAct = time.monotonic() - start
        try:
            sentence = uart.readline().decode("utf-8", errors="ignore").strip()
            if testNMEA(sentence,'$GNRMC'):
                #print(str(timeAct)+sentence)

                datas = {
                    'time':timeAct,
                    'NMEA':datasGPS(sentence)[0],
                    'lattD':datasGPS(sentence)[1],
                    'longD':datasGPS(sentence)[2],
                }

                shared_data['gpsDatas'] = datas

                coordTxt.write(f"\n{datas['lattD']},{datas['longD']}")
                coordTxt.flush()
                dataTxt.write("\n{},{},{},{}".format(*list(datas.values())))
                dataTxt.flush()

        except Exception as err:
            print(err)
            uart.close()
            uart.open()
