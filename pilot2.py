################################################################################
# Xeon rocket parafoil control script, gets all datas and control the parafoil #
################################################################################

# import general librairies
import time
import RPi.GPIO as GPIO
from util_calculations import pointIsGood, angle_to_percent

class Servo:
    
    def __init__(self, pin, side):
        self.pin = pin
        GPIO.setup(pin, GPIO.OUT)
        self.pwm = GPIO.PWM(pin, frequenceServ)
        self.uses = 0
        if side in ("g", "l"):
            self.dicPos = {"start": angle_to_percent(0), "mid": angle_to_percent(90), "max": angle_to_percent(180)}
        else:
            self.dicPos = {"start": angle_to_percent(180), "mid": angle_to_percent(90), "max": angle_to_percent(0)}

    def go(self, pos):
        if self.uses == 0:
            self.pwm.start(self.dicPos[pos])
        else:
            self.pwm.ChangeDutyCycle(self.dicPos[pos])
        self.uses += 1

    def goFineTune(self, angle_degree):
        self.pwm.ChangeDutyCycle(angle_to_percent(angle_degree))
    
    def suddenMove(self,func,timer):
        func
        time.sleep(timer)
        self.go("start")
    
    def kill(self):
        self.pwm.stop()

def go(where, strength="max"):
    """'reset' for both at start, 'full' for both at max, 'x','y' to go to x side with y as 'start', 'mid' or 'max'"""
    whereServ = {"g":servG,"d":servD}
    servG.go("start")
    servD.go("start")
    if where!="reset" and where!="full": 
        whereServ[where].go(strength)
    elif where=="full": 
        servG.go("max")
        servD.go("max")
    else:
        pass


def set_background_color(color):
    color_codes = {
        "black": "\033[40m",
        "red": "\033[41m",
        "green": "\033[42m",
        "yellow": "\033[43m",
        "blue": "\033[44m",
        "magenta": "\033[45m",
        "cyan": "\033[46m",
        "white": "\033[47m",
        "bright_black": "\033[100m",
        "bright_red": "\033[101m",
        "bright_green": "\033[102m",
        "bright_yellow": "\033[103m",
        "bright_blue": "\033[104m",
        "bright_magenta": "\033[105m",
        "bright_cyan": "\033[106m",
        "bright_white": "\033[107m"
    }
    
    if color in color_codes:
        print(f"{color_codes[color]}\033[2J\033[H", end='')
    else:
        print("Color not supported")

def switchOffLeds(leds):
    for led in leds:
        GPIO.output(led,GPIO.LOW)


def mainLoop(shared_data):


    ##### Initialisation #####


    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    global leds 
    leds = {'bleu':20,'verte':21,'jaune':16,'orange':12}


    optoIn1 = 17
    optoIn2 = 22 # Jack
    optoOt1 = 2
    optoOt2 = 4

    dual1 = 6
    dual2 = 5

    global frequenceServ

    frequenceServ = 50

    servG = Servo(13, "g")
    servD = Servo(19, "d")

    switch_pin = 26

    timer = 15        # seconds after cone opens
    timeDual = 4      # timer of rotation for dual
    minTempDual = 57  # min timer
    maxTempDual = 79 # max temp dual
    altiDual = 430    # altitude where the dual is ignited

    startTime = time.monotonic()

    for compo in list(leds.values())+[optoOt1, optoOt2,dual1,dual2]:
        GPIO.setup(compo,GPIO.OUT)

    for compo in [optoIn1, optoIn2, switch_pin]:
        GPIO.setup(compo,GPIO.IN, GPIO.PUD_DOWN)

    for led in list(leds.values()):
        GPIO.output(led, GPIO.HIGH)
        time.sleep(0.75)

    current_color = None


    ##### Boucle principale #####


    runningRamp = True
    runningUp   = True
    runningDown = True

    while runningRamp:

        ##### En rampe #####

        timeAct = time.monotonic()-startTime

        stateO1, stateO2 = GPIO.input(optoIn1), GPIO.input(optoIn2)
        switch_state = GPIO.input(switch_pin)

        if switch_state == GPIO.HIGH:
            if current_color != "green":
                set_background_color("green")
                current_color = "green"
                print("Switch is ON")
                GPIO.output(dual2,GPIO.HIGH)
        else:
            if current_color != "red":
                set_background_color("red")
                current_color = "red"
                print("Switch is OFF")
                GPIO.output(dual2,GPIO.LOW)

        if stateO2==GPIO.HIGH:
            # Arduino ping for take off
            GPIO.output(leds['verte'], GPIO.LOW)
            print("Ping")
            set_background_color("blue")

            takeOffTime = time.monotonic()

            while runningUp:

                ##### En ascension et descente sous drag #####

                timeFromTakeOff = time.monotonic()-takeOffTime

                alti = shared_data.get('data', {'alti':0})['alti']
                nvSecu = shared_data.get('nvSecu', 0)
                set_background_color('yellow')

                if timeFromTakeOff>= minTempDual and timeFromTakeOff<=maxTempDual:
		    # Si alt ok et on rst dans la zone
                    if True: #alti<=altiDual and nvSecu==1:

                        ##### Ouverture parafoil #####
                        set_background_color('cyan')
                        print("Openning Dual")
                        GPIO.output(dual1, GPIO.HIGH)
                        time.sleep(timeDual)
                        GPIO.output(dual1, GPIO.LOW)


                        ##### Initialisation #####

                        time.sleep(1)

                        while runningDown : 

                            #####   Pilotage et verification zone   #####

                            nvSecu = shared_data.get('nvSecu', 0)

                            if nvSecu==1:
                                # On est dans la zone
                                GPIO.output(leds['bleu'], GPIO.HIGH)
                                GPIO.output(leds['orange'], GPIO.LOW)
                                set_background_color['green']

                                # Manips de pilotage ici


                            elif nvSecu==3:
                                # On sort de la zone, mise en sécu
                                time.sleep(0.1)
                                if nvSecu==3:
                                    GPIO.output(leds['orange'], GPIO.HIGH)
                                    GPIO.output(leds['bleu'], GPIO.LOW)

                                    set_background_color('magenta')
                                    go('d','max') # Mettre les servos en vrille
                                    time.sleep(3)
                                    runningRampe = False
                                    runningUp = False

                else:
                # fin de la scrutatation d'alti et de zone
                    #Fin du programme
                    continue
        else:
            GPIO.output(leds['verte'], GPIO.HIGH)
            print("No ping")
            GPIO.output(dual1, GPIO.LOW)

        """print(f"\n\n\n\n\nPILOT: \n data : {gyroAltiDatas}, \n gps_data : {gpsDatas}, \n nvSecu : {nvSecu}")
        if isinstance(gpsDatas,dict): print(gpsDatas['lattD'])"""
        time.sleep(0.1)
