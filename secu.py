import time
from random import randint
from util_calculations import pointIsGood, logText, set_update_rate

def secu(shared_data):

    startTime = time.monotonic()

    while True:

        timeAct = round(time.monotonic() - startTime,2)

        try:
            gyroAltiDatas = shared_data.get('data', 0)
            gpsDatas = shared_data.get('gpsDatas', 0)
        except Exception as err:
            logText("secu 1",err,timeAct)
            continue

        try:
            if isinstance(gpsDatas, dict):
                #print("toto1")
                point_inside = pointIsGood((gpsDatas['lattD'], gpsDatas['longD']))
                #print("toto2")
                print(f"SECU : {gpsDatas['lattD']}, {gpsDatas['longD']} => {point_inside}")

                if point_inside: shared_data['nvSecu'] = 1
                else:            shared_data['nvSecu'] = 3
            else:
                time.sleep(0.1)
                #print("toto3")
                continue
        except Exception as err:
            logText("secu 2",err,timeAct)
            time.sleep(0.1)
            continue
        time.sleep(0.1)
