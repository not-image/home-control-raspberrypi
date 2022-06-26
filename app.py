import requests
import serial
import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM) # General purpose in and out
GPIO.setwarnings(False)
TRIG = 23 # Para el sensor de proximidad
ECHO = 24
GPIO_PIR = 27 # Entrada sensor de movimiento
GPIO.setup(TRIG, GPIO.OUT) # Se le asigna el modo a cada GPIO (in/out)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(GPIO_PIR, GPIO.IN)
ser = serial.Serial("/dev/ttyACM0", 9600) # Temperatura via arduino
ser.flushInput()
# GPIO.setup(17, GPIO.OUT)
# GPIO.output(17, GPIO.LOW)
# GPIO.setup(16, GPIO.OUT)
# GPIO.output(16, GPIO.LOW)

BASE_URL = "https://8000-deinys-smarthomebackend-k4m8zj621op.ws-us46.gitpod.io"

# Numero de serial del controlador
def get_serial():
    cpu_serial = "0000000000000000"
    try:
        f = open("/proc/cpuinfo", "r")
        for line in f:
            if line[0:6] == "Serial":
                cpu_serial = line[10:26]
        f.close()
        return cpu_serial
    except:
        cpu_serial = "ERROR000000000"
    return "err"
# Medida de la temperatura
def get_temperature():
    lineBytes = ser.readline()
    temperature = lineBytes.decode("utf-8").strip()
    print(temperature)
    return temperature
# Medida del movimiento
def get_motion():
    if GPIO.input(GPIO_PIR):
        print(True)
        return True
    else:
        print(False)
        return False
# Medida de distancia (proximidad)
def get_sonar():
    GPIO.output(TRIG, False)
    time.sleep(1)
    GPIO.output(TRIG, True)
    time.sleep(0.0001)
    GPIO.output(TRIG, False)
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
    pulse_duration = pulse_end - pulse_start
    distance = pulse_duration * 17150
    distance = round(distance, 2)
    print(distance)
    return distance
# Guarda la nueva medida de temperatura y manda el post a la API

count = 0

def start_temperature(token):
    global count
    count = count + 1
    if count == 5:
        temperature_data = get_temperature()
        # SUSTITUIR None POR LA INFORMACION RECIBE LA VARIABLE temperature_data SI SE CORRE LA FUNCION get_temperature() CUANDO EL SENSOR ESTA DESCONECTADO
        if temperature_data is not None:
            res = requests.post(
                f"{BASE_URL}/create",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                },
                json={"device_type": "thermostat", "device_data": f"{temperature_data}"},
            )
            content = res.json()
            print(content["response"], res.status_code)
            count = 0
        else:
            print("Temperature sensor data is incorrect.")
            count = 0
# Guarda la nueva medida de movimiento y manda el post a la API
past_data = False
def send_motion(data,token):
    global past_data
    motion_data = data
    if motion_data is not None:
        if past_data != motion_data:
            res = requests.post(
                f"{BASE_URL}/create",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                },
                json={"device_type": "motion", "device_data": f"{motion_data}"},
            )
            content = res.json()
            # print(motion_data, "---Data Actual")
            # print(past_data, "---Past")
            print(content["response"], res.status_code)
            past_data = motion_data
        else:
            print("no ha habido cambio de movimiento")
    else:
        print("Motion sensor data is incorrect.")
def start_motion(token):
    if GPIO.input(GPIO_PIR):
        print("SE DETECTO MOVIMIENTO")
        send_motion(True, token)
    else:
        print("NO HAY")
        send_motion(False, token)
# Guarda la nueva medida de distancia y manda el post a la API
count_level = 0

def start_sonar(token):
    global count_level
    count_level = count_level + 1
    if count_level == 3:
        sonar_data = get_sonar()
        if sonar_data is not None:
            res = requests.post(
                f"{BASE_URL}/create",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                },
                json={"device_type": "sonar", "device_data": f"{sonar_data}"},
            )
            content = res.json()
            print(content["response"], res.status_code)
            count_level = 0
        else:
            print("Sonar sensor data is incorrect.")
            count_level = 0
# Funcion recursiva principal
def run_requests(token):
    start_motion(token)
    start_temperature(token)
    start_sonar(token)
    time.sleep(4)
    run_requests(token)
# verificar que el controlador existe SOLO UNA VEZ cambiar
# Funcion inicial para validar controlador
def init():
    controller_id = get_serial()
    print(controller_id)
    res = requests.post(
        f"{BASE_URL}/validate",
        headers={
            "Content-Type": "application/json",
        },
        json={"controller_sn": controller_id},
    )
    content = res.json()

    if res.status_code == 200:
        token = content["response"]
        run_requests(token)
    else:
        print(content["response"])
        time.sleep(4)
        init()
init()

# res = requests.get(f"{BASE_URL}/green-on")
# if res.ok:
#     GPIO.output(16, GPIO.HIGH)
#     print("Green Led ON")

if GPIO.input(GPIO_PIR):
    time.sleep(2)
    res = requests.post(
        f"{BASE_URL}/create",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        json={"device_type": "motion", "device_data": True},
    )
    content = res.json()
    print(content["response"], res.status_code)