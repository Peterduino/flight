################################################################################
# Xeon rocket parafoil control script, gets all datas and control the parafoil #
################################################################################

# import general librairies
import time
import RPi.GPIO as GPIO
from util_calculations import angle_to_percent

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
        eval(func)
        time.sleep(timer)
        self.go("start")
    
    def kill(self):
        self.pwm.stop()

def go(where, strength="max"):
    """'reset' for both at start, 'full' for both at max, 'x','y' to go to x side with y as 'start', 'mid' or 'max'"""
    whereServ = {"g":servG,"d":servD}
    servG.go("start")
    servD.go("start")
    if where in ['d','g']: 
        whereServ[where].go(strength)
    elif where=="full": 
        servG.go("max")
        servD.go("max")
    elif where=='vrilleS':
        servG.go("start")
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


##### Fonctions de pilotage #####

    




def mainLoop(shared_data):


    ##### Initialisation #####


    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    global leds 
    leds = {'bleu':20,'verte':21,'jaune':16,'orange':12}


    optoIn1 = 17
    optoIn2 = 22 # Jack
    optoOt1 = 27
    optoOt2 = 4

    dual1 = 6
    dual2 = 5

    global frequenceServ
    frequenceServ = 50

    switch_pin = 26

    timer = 15        # seconds after cone opens
    timeDual = 4      # timer of rotation for dual
    minTempDual = 57  # min timer
    maxTempDual = 79  # max temp dual
    altiDual = 430    # altitude where the dual is ignited

    landingPoint = (43.2005972222,-0.0628638889)                                                             # EARTHSHAKING !!!!!

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

            print("totoSer1")

            while runningUp:

                ##### En ascension et descente sous drag #####

                timeFromTakeOff = time.monotonic()-takeOffTime

                alti = shared_data.get('data', {'alti':0})['alti']
                print(f"alti : {alti}")
                nvSecu = shared_data.get('nvSecu', 0)
                print(f"nvSecu : {nvSecu}")
                set_background_color('yellow')

                if timeFromTakeOff>= minTempDual and timeFromTakeOff<=maxTempDual:
		        # Si alti ok et on est dans la zone
                    if nvSecu==1:

                        ##### Ouverture parafoil #####
                        set_background_color('cyan')
                        print("Openning Dual")
                        GPIO.output(dual1, GPIO.HIGH)
                        time.sleep(timeDual)
                        GPIO.output(dual1, GPIO.LOW)
                        
                        global servG, servD

                        servG = Servo(13, "g")
                        servD = Servo(19, "d")

                        print("totoSer2")

                        go('reset')

                        print("totoSer3")

                        print("servos good")


                        time.sleep(1)


                        comptP1 = 0 # Pilotage
                        comptP2 = 0 # 
                        ccomptPoints = 0 

                        comptPBgps  = 0
                        FlightState = 0 # 1 tt est parfait ; 2 pas GPS
                        
                        turnCredits = 0
                        comptAlti = 0

                        points = []
                        vitesse = 5
                        go('reset')

                        while runningDown : 

                            #####   Pilotage et verification zone   #####
                            
                            # Check secu zone


                            if comptAlti==0:
                                # au debut du compteur prendre une valeure d'alti et avancer de 1
                                altiOld = shared_data.get('data', {'alti':0})['alti']
                                comptAlti=1
                            elif comptAlti==10:
                                # a la fin du compteur prendre une valeure d'alti, calculer la vitesse et la stocker
                                altiNew = shared_data.get('data', {'alti':0})['alti']
                                vitesse = altiOld-altiNew
                                tmpVitesse = vitesse
                                comptAlti=0 # Reinitialiser le compteur
                            else :
                                # entre les bornes, augmenter le compteur et conserver la valeure de vitesse
                                comptAlti+=1
                                vitesse = tmpVitesse
                  

                            nvSecu = shared_data.get('nvSecu', 0)

                            print(f"nvSecu : {nvSecu}")

                            if nvSecu==3 or vitesse<=3.:
                                ##### If out of zone #####
                                #time.sleep(0.1)
                                print("toto GERRR")
                                #if nvSecu==3:
                                #GPIO.output(leds['orange'], GPIO.HIGH)
                                #GPIO.output(leds['bleu'], GPIO.LOW)

                                set_background_color('magenta')
                                print("OUT OF THE ZONE, FLIGHT CANCEL")
                                go('d','max') # Mettre les servos en vrille
                                time.sleep(3)
                                runningRampe, runningUp, runningDown = False, False, False

                                GPIO.cleanup()

                            else:
                                ##### If in zone #####
                                GPIO.output(leds['bleu'], GPIO.HIGH)
                                GPIO.output(leds['orange'], GPIO.LOW)
                                set_background_color('green')

                                # Manips de pilotage ici

                                #positionActuelle = (datasGPS['lattD'], datasGPS['longD'])

                                """if len(points) < 10:
                                    go("reset")
                                    points.append(positionActuelle)
                                else:
                                    whereServ = {"g":servG,"d":servD}

                                    a, b, sens_deplacement = line(points)                                                                               # créer la droite
                                    angle, sens_rotation = calculer_correction_trajectoire(a, b, sens_deplacement, points[len(points)-1], landingPoint) # traiter

                                    if turnCredits==0:
                                        if angle>=2 and angle<=30:
                                            go(whereServ[sens_rotation],'mid')
                                            turnCredits = 10
                                        elif angle>30 and angle<=100:
                                            go(whereServ[sens_rotation],'max')
                                            turnCredits = 10
                                        elif angle>100:
                                            go(whereServ[sens_rotation],'max')
                                            turnCredits = 20
                                    else:
                                        turnCredits-=1
                                        if turnCredits==0:
                                            go("reset")
                                            points=[]"""



                            #Stoquer nvSecu
                            #Stoquer FlightState                            
                            time.sleep(0.1)







                else:
                # fin de la scrutatation d'alti et de zone
                    #Fin du programme
                    continue
                time.sleep(0.1)

        else:
            GPIO.output(leds['verte'], GPIO.HIGH)
            print("No ping")
            GPIO.output(dual1, GPIO.LOW)

        """print(f"\n\n\n\n\nPILOT: \n data : {gyroAltiDatas}, \n gps_data : {gpsDatas}, \n nvSecu : {nvSecu}")
        if isinstance(gpsDatas,dict): print(gpsDatas['lattD'])"""
        time.sleep(0.1)





"""datasGPS = shared_data.get('datasGPS', 0)

                            # Check si le GPS est actif

                            if (not isinstance(datasGPS, dict)) or (datasGPS['lattD']==None) or (datasGPS['lattD']==""):
                                
                                comptPBgps+=1
                                FlightState = 2
                                print(f"WRONG NMEA : {datasGPS['NMEA']}")
                                if comptPBgps >= 30: # attendre 3 sec

                                    GPIO.output(leds['orange'], GPIO.HIGH)
                                    GPIO.output(leds['bleu'], GPIO.LOW)

                                    set_background_color('magenta')
                                    print("BAD GPS, FLIGHT CANCEL")
                                    go('d','max') # Mettre les servos en vrille
                                    time.sleep(3)
                                    runningRampe, runningUp, runningDown = False, False, False

                                    GPIO.cleanup()                               

                                continue
                            else:
                                comptPBgps  = 0
                                FlightState = 1"""