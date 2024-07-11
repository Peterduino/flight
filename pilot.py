################################################################################
# Xeon rocket parafoil control script, gets all datas and control the parafoil #
################################################################################

# import general librairies
import time
import RPi.GPIO as GPIO
from util_calculations import pointIsGood

def switchOffLeds(leds):
    for led in leds:
        GPIO.output(led,GPIO.LOW)

def pilot(shared_data):

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    leds = [20,21,16,12]
    jack = 17

    startTime = time.monotonic()

    for led in leds:
        GPIO.setup(led,GPIO.OUT)
    GPIO.output(21, GPIO.HIGH)
    GPIO.output(16, GPIO.HIGH)

    while True:
        timeAct = time.monotonic()
        try:
            gyroAltiDatas = shared_data.get('data', 0)
            gpsDatas = shared_data.get('gpsDatas', 0)
            nvSecu = shared_data.get('nvSecu', 0)
            pass
        except:
            with open("./logs/pilot.txt", "a") as file: 
                file.write(str(timeAct-startTime)," : Error reading datas on shared values")
            continue
        if nvSecu==1:
            GPIO.output(20, GPIO.HIGH)
            GPIO.output(12, GPIO.LOW)
        else:
            GPIO.output(12, GPIO.HIGH)
            GPIO.output(20, GPIO.LOW)



        print(f"\n\n\n\n\nPILOT: \n data : {gyroAltiDatas}, \n gps_data : {gpsDatas}, \n nvSecu : {nvSecu}")
        if isinstance(gpsDatas,dict): print(f"{gpsDatas['lattD']}")
        time.sleep(0.2)
