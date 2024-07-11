
import math
import ast
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon
from shapely.affinity import scale
import time

def angle_between_points(A, B, C):
    """Returns in degrees the angle ABC"""
    AB = [B[0] - A[0], B[1] - A[1]]
    BC = [C[0] - B[0], C[1] - B[1]]
    angle_AB = math.atan2(AB[1], AB[0])
    angle_BC = math.atan2(BC[1], BC[0])
    angle_ABC = math.degrees(angle_BC - angle_AB)
    return angle_ABC

def dmmm_to_dd(dmmm):
    """Converts nmea coordinates to decimal degrees coordinates"""
    dd = (math.floor(float(dmmm))//100) + ((float(dmmm)-((float(dmmm)//100)*100)) / 60 )
    #dd = degrees         + minutes             / 60
    return dd

def listNMEA(sentence):
    """Returns sentence:str as list splitted between commas"""
    liste = sentence.split(",")
    return liste

def latOf(sentence):
    """Returns the lattitude:int in DD written in the 4th element of sentence:str"""
    lat = dmmm_to_dd(listNMEA(sentence)[3])
    lat = round(lat,6)
    return lat if listNMEA(sentence)[4] == 'N' else -lat

def longOf(sentence):
    """Returns the longitude:int in DD written in the 4th element of sentence:str"""
    lon = dmmm_to_dd(listNMEA(sentence)[5])
    lon = round(lon,6)
    return lon if listNMEA(sentence)[6] == 'E' else -lon

def line(points):
    """Return (a, b):ints from the linear ajustement of all points in points:list"""
    n = len(points)
    sum_x = sum(point[0] for point in points)
    sum_y = sum(point[1] for point in points)
    sum_x_squared = sum(point[0] ** 2 for point in points)
    sum_xy = sum(point[0] * point[1] for point in points)

    a = (n * sum_xy - sum_x * sum_y) / (n * sum_x_squared - sum_x ** 2)
    b = (sum_y - a * sum_x) / n

    return a, b
    # Test with :
    #points = [(1, 1), (3, 2), (5, 1), (7, 2), (9, 1)]
    #a, b = line(points)
    #print("a =", a, "et b =", b)

def ThreeUpletFrom(lst):
    return ast.literal_eval(','.join(lst))
    
def decodeDatas(datas):
    """BETAAAAAAAAAAA NOT Working"""
    dico = datas.split(",")
    datasD = {
        'time': dico[0],
        'temp': dico[1],
        'press': dico[2],
        'alti': dico[3],
        'accel': ThreeUpletFrom(dico[4:7]),
        'magne': ThreeUpletFrom(dico[7:10]),
        'gyro': ThreeUpletFrom(dico[10:13]),
        'euler': ThreeUpletFrom(dico[13:16]),
        'linAc': ThreeUpletFrom(dico[16:19]),
        'gravi': ThreeUpletFrom(dico[19:22])
    }
    datasL = [
        dico[0],
        dico[1],
        dico[2],
        dico[3],
        *[ThreeUpletFrom(dico[i:i+3]) for i in range(4, len(dico), 3)]
    ]
    return datasD

def angle_to_percent(angle) :
    
    assert 0<=angle<=180, "Angle provided not in between 0 and 180"

    start = 4
    end = 12.5
    ratio = (end - start)/180

    return start + angle * ratio

def calculer_correction_trajectoire(a, b, sens_deplacement, position_A, position_B):
    
    x_A_projete = (a*(position_A[0]) + position_A[1] - b)/(a**2 + 1)
    y_A_projete = a * x_A_projete + b
    position_A_projete = (x_A_projete, y_A_projete)

    if sens_deplacement == "g":
        angle_trajectoire_droite = math.pi / 2 - math.atan(a)
    elif sens_deplacement == "d":
        angle_trajectoire_droite = -math.pi / 2 - math.atan(a)
    else:
        raise ValueError("Le sens de déplacement doit être 'g' ou 'd'.")

    direction_AB = math.atan2(position_B[1] - position_A_projete[1], position_B[0] - position_A_projete[0])

    correction_trajectoire = direction_AB - angle_trajectoire_droite

    sens_rotation = "gauche" if correction_trajectoire > 0 else "droite"

    return abs(math.degrees(correction_trajectoire)), sens_rotation

def logText(script, log, time):
    with open(f"./logs/{script}.txt", "a") as file: 
        file.write(str(time)+","+str(log))
    print(script+str(log))


##### GPS #####


def testNMEA(sentence,strFiltre):
    """Returns True or False depending on validity of sentence:str depending on some factors"""
    if sentence.startswith(strFiltre) and len(listNMEA(sentence))==13 and listNMEA(sentence)[3]!=None and listNMEA(sentence)[5]!=None and listNMEA(sentence)[3]!='' and listNMEA(sentence)[5]!='':
        return True
    return False

def waitUntilNMEA(uart,strFiltre):
    """Returns either an NMEA sentence:str (when provided) or an error message:str if not convinient"""
    while True:
        try :
            sentence = uart.readline().decode("utf-8", errors="ignore").strip()
            # now return it only if correct
            if testNMEA(sentence,strFiltre):
                return sentence
            elif (sentence.startswith('$GNRMC')) and len(listNMEA(sentence))!=13:
                return "! TRAM ERROR"
            elif (sentence.startswith('$GNRMC')) and listNMEA(sentence)[3]!='':
                return "! NO GPS FIX"
            
        except KeyboardInterrupt:
            break
        except:
            uart.close()
            uart.open()

def datasGPS(sentence):
    """Returns the 3-uple (NMEA sentence:str, latitude:str, longitude:str)"""
    if sentence.startswith("!"):
        return "!", "!", "!"
    else:
        return sentence, str(latOf(sentence)), str(longOf(sentence)),

def send_ubx_message(serial_port, msg):
    serial_port.write(bytearray(msg))
    time.sleep(0.1)

def set_update_rate(serial_port, rate_ms):
    msg = [
        0xB5, 0x62,
        0x06, 0x08,
        0x06, 0x00,
        rate_ms & 0xFF, (rate_ms >> 8) & 0xFF,
        0x01, 0x00,
        0x00, 0x00
    ]
    ck_a = 0
    ck_b = 0
    for i in range(2, len(msg)):
        ck_a = (ck_a + msg[i]) & 0xFF
        ck_b = (ck_b + ck_a) & 0xFF
    msg.append(ck_a)
    msg.append(ck_b)

    send_ubx_message(serial_port, msg)



##### Polygon gestion for ZAS zones #####



def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance

def is_point_in_polygon(polygon_points, point):
    polygon = Polygon(polygon_points)
    p = Point(point)
    return polygon.contains(p)

def reduce_polygon_area(polygon_points, reduction_percentage):
    polygon = Polygon(polygon_points)
    if not polygon.is_valid or polygon.is_empty:
        raise ValueError("Invalid polygon")
    
    original_area = polygon.area
    target_area = original_area * (1 - reduction_percentage / 100)
    
    scale_factor = math.sqrt(target_area / original_area)
    centroid = polygon.centroid
    reduced_polygon = scale(polygon, xfact=scale_factor, yfact=scale_factor, origin=centroid)
    
    return reduced_polygon

def expand_polygon_area(polygon_points, expansion_percentage):
    polygon = Polygon(polygon_points)
    if not polygon.is_valid or polygon.is_empty:
        raise ValueError("Invalid polygon")
    
    original_area = polygon.area
    target_area = original_area * (1 + expansion_percentage / 100)
    
    scale_factor = math.sqrt(target_area / original_area)
    centroid = polygon.centroid
    expanded_polygon = scale(polygon, xfact=scale_factor, yfact=scale_factor, origin=centroid)
    
    return expanded_polygon

def plot_polygons(original_polygon, reduced_polygon, red_zone_polygon, expanded_red_zone_polygon, point):
    fig, ax = plt.subplots()
    
    # White Zone
    original_lat, original_lon = original_polygon.exterior.xy
    ax.fill(original_lon, original_lat, alpha=0.5, fc='blue', ec='blue', label='Zone blanche')
    
    # White zone with margin
    reduced_lat, reduced_lon = reduced_polygon.exterior.xy
    ax.fill(reduced_lon, reduced_lat, alpha=0.5, fc='green', ec='green', label='Zone blanche avec marge')
    
    # Red zone
    red_zone_lat, red_zone_lon = red_zone_polygon.exterior.xy
    ax.fill(red_zone_lon, red_zone_lat, alpha=0.5, fc='red', ec='red', label='Zone rouge')
    
    # Red zone with margin
    expanded_red_zone_lat, expanded_red_zone_lon = expanded_red_zone_polygon.exterior.xy
    ax.fill(expanded_red_zone_lon, expanded_red_zone_lat, alpha=0.3, fc='orange', ec='orange', label='Zone rouge avec marg')
    
    # Lunch point
    lat, lon = point
    ax.plot(lon, lat, 'go', label='Point',c="red")
    
    plt.legend()
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Carte de ZAS')
    plt.grid(True)
    ax.set_aspect('equal', 'box')
    plt.show()

def pointIsGood(point):

    """file_path = '/mnt/data/your_file.txt'
    with open(file_path, 'r') as file:
        first_line = file.readline().strip()

        eval(first_line)"""
    #ZAS
    """polygon_points = [(43.24184301098239, -0.03985558918725263),(43.24236968149143, -0.03969046267809829),(43.242678529363516, -0.040904365664313894),(43.242194125160964, -0.04116767550323567)]
    polygon_points = [
        (43.242390, -0.041380),
        (43.241690, -0.041820),
        (43.241860, -0.042280),
        (43.242450, -0.041910)
    ] # FOOT"""

    polygon_points = [(43.21830103040428, -0.07011136967427564), (43.2213105382539, -0.04938286301931613), (43.214567133356724, -0.04958847247852908), (43.20773958223958, -0.04657384268508656), (43.193425944370816, -0.0631572333740626), (43.19523691736566, -0.07163331869620779), (43.21830103040428, -0.07011136967427564)]
    #polygon_points = [(43.24113822123081, -0.04008916276647504),(43.241814776944175, -0.0430153030407418),(43.24386756781792, -0.04195298689769278),(43.2434412602798, -0.03932582182536197)] # Zone qualif
    # Whole Camp
    """polygon_points = [
        (43.24272595827425, -0.04151086538385301),
        (43.24288827119201, -0.042081278016667834),
        (43.243068290467775, -0.04195650025323959),
        (43.24294198191685, -0.04139500031781251)]
    """
    red_zone_points = [(43.209472, -0.061250),(43.216675, -0.056886),(43.215200, -0.051136),(43.203322, -0.057242),(43.203625, -0.060708)]

    reduction_percentage = 0
    expansion_percentage = 0

    """file_path = './Xeon/zas.conf'
    with open(file_path, 'r') as file:
        lines = file.readline().strip()
    eval(lines)
    print("bernard0.5")"""
    """for line in lines:
        command = line.strip()
        if command and not command.startswith('#'):
            eval(command)
            print(variable1)"""

    try:
        original_polygon = Polygon(polygon_points)
        reduced_polygon = reduce_polygon_area(polygon_points, reduction_percentage)
        red_zone_polygon = Polygon(red_zone_points)
        expanded_red_zone_polygon = expand_polygon_area(red_zone_points, expansion_percentage)


        point_inside = is_point_in_polygon(polygon_points, point)
        point_inside_reduced = reduced_polygon.contains(Point(point))
        point_inside_red_zone = red_zone_polygon.contains(Point(point))
        point_inside_expanded_red_zone = expanded_red_zone_polygon.contains(Point(point))

        #print("Point inside original polygon:", point_inside)
        #print("Point inside reduced polygon:", point_inside_reduced)
        #print("Point inside red zone polygon:", point_inside_red_zone)
        #print("Point inside expanded red zone polygon:", point_inside_expanded_red_zone)

        if (point_inside, point_inside_reduced)==(True,True):
            point_is_good = True
        else:
            point_is_good = False
        
        #print("Point is good", str(point_is_good))

        return point_is_good
        
        #plot_polygons(original_polygon, reduced_polygon, red_zone_polygon, expanded_red_zone_polygon, point)
    except ValueError as e:
        print(f"Error pointIsGood dans UC: {e}")

if __name__=='__main__':
    pointIsGood((43.218436, -0.047333)) # test

"""def determiner_virage(A0,A, point_final):

    vec_A_Aplus = np.array(A) - np.array(A0)
    vec_A_point_final = np.array(point_final) - np.array(A)
    produit_vectoriel = np.linalg.det([vec_A_Aplus, vec_A_point_final])
    
    if produit_vectoriel > 0: # gauche
        return -1, produit_vectoriel
    elif produit_vectoriel < 0: # droit
        return 1, produit_vectoriel
    else:
        return 0, produit_vectoriel
"""
"""if __name__ == '__main__':
    
    #test determiner_virage()
    
    point_final = np.array([0, -2])
    A0 = np.array([0, 0])
    A = np.array([2, 0])

    res = determiner_virage(A0, A, point_final)[0]

    if res == -1:
        print("Gauche")
    elif res == 1:
        print("Droite")
    else:
        print("Pas de virage")


if __name__=='__main__':
    
    tram = "0,1,2,3,(4,5,6),(7,8,9),(10,11,12),(13,14,15),(16,17,18),(19,20,21)"
    tramD = decodeDatas(tram)

    for el in tramD:
        print(str(el)+" : "+str(tramD[el]))

On vise le point si on est à + de 5m du point selon les coord GPS donc on doit avoir une correspondance coords metres
A 5m on frene
On tourne 1 sec à chaque fois

Datas :
    - Droite
    - Deux derniers projetés hortogonaux 
    
    
"""
