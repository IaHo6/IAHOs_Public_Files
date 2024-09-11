import socket
import time
import errno
import sys
from datetime import datetime
import re
from rpi_ws281x import *
import argparse
from subprocess import call

LED_COUNT      = 39      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 200     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53
STEPS = 47

HEADER_LENGTH = 10
IP = "127.0.0.1"
PORT = 1236

sun_start_time_str = '07:00:00'
sun_pause_time_str = '22:00:00'
sun_start_time = datetime.strptime(sun_start_time_str, '%H:%M:%S').time()
sun_pause_time = datetime.strptime(sun_pause_time_str, '%H:%M:%S').time()

rainbowrun = False
sunpauseedit = False
customcolor = False
morsecode = False
morserun = False
rainbowCirclerun = False
rainbowallrun = False
nerdRun = False
sunRun = False
x = 0
y = 0
z = 0
u = 0
count = 0
countflanke = 0
morse_list = []

shift = 0


def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)


def wheel(pos):
    """Generate rainbow colors across 0-255 positions."""
    if pos < 85:
        return Color(pos * 3, 255 - pos * 3, 0)
    elif pos < 170:
        pos -= 85
        return Color(255 - pos * 3, 0, pos * 3)
    else:
        pos -= 170
        return Color(0, pos * 3, 255 - pos * 3)
    

def rainbow(strip, x, wait_ms=20):
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, wheel((i+x) & 255))
    strip.show()
    time.sleep(wait_ms/1000.0)


def rainbowCycle(strip, w,  wait_ms=20):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, wheel((int(i * 256 / strip.numPixels()) + w) & 255))   
    strip.show()
    time.sleep(wait_ms/1000.0)


def circle(strip, color, lenght = 9, wait_ms = 50):
    for i in range(39):
        for j in range(lenght):
            if not i-j < 0:
                strip.setPixelColor((i-j), color)
        if not i-lenght < 0:
            strip.setPixelColor((i-lenght), 0)
        if not i+38-lenght > 38:
            strip.setPixelColor((i+38-lenght), 0)
        strip.show()
        time.sleep(wait_ms/1000)


def colorcustom(input_str):
    global color_list
    # Regular expression, um den Namen und den RGB-Code zu extrahieren
    pattern = r'([a-z]+)(\d{1,3})/(\d{1,3})/(\d{1,3})'
    
    # Sucht nach dem Muster im Eingabestring
    match = re.match(pattern, input_str)
    
    if match:
        # Extrahiert den Namen und die RGB-Werte
        name = match.group(1)
        # Extrahiere die RGB-Werte als Ganzzahlen
        rgb_values = [int(match.group(i)) for i in range(2, 5)]
        
        # Überprüfe, ob die RGB-Werte im Bereich von 0 bis 255 liegen
        if all(0 <= value <= 255 for value in rgb_values):
            # Erstellt das Dictionary
            
            return name, rgb_values
        else:
            raise ValueError("RGB-Werte müssen zwischen 0 und 255 liegen.")
    else:
        raise ValueError("Ungültiges Format.")
    

def nerd(strip, color, num, wait_ms = 500):
    binary_x = format(num, '039b')
    x = 0
    for bit in binary_x:
        if bit == '1':
            strip.setPixelColor(x, color)
        else:
            strip.setPixelColor(x, 0)
        x += 1
        
    strip.show()
    time.sleep(wait_ms/1000)

    
def time_run():
    start_time = datetime.strptime('00:00:00', '%H:%M:%S').time()
    current_time = datetime.now().time()
    time_difference = datetime.combine(datetime.today(), current_time) - datetime.combine(datetime.today(), start_time)
    seconds_difference = time_difference.total_seconds()
    return seconds_difference


def sun_rise(strip, variables): 
    strip.setPixelColor(variables[0], 0)
    strip.setPixelColor(variables[1], Color(24, 6, 0))
    strip.setPixelColor(variables[2], Color(63, 24, 0))
    strip.setPixelColor(variables[3], Color(127, 48, 0))
    strip.setPixelColor(variables[4], Color(191, 82, 0))
    strip.setPixelColor(variables[5], Color(255, 120, 0))
    strip.setPixelColor(variables[6], Color(191, 82, 0))
    strip.setPixelColor(variables[7], Color(127, 48, 0))
    strip.setPixelColor(variables[8], Color(63, 24, 0))
    strip.setPixelColor(variables[9], Color(24, 6, 0))
    strip.setPixelColor(variables[10], 0)
    strip.show()
    

def calculate_sun(strip, count, shift):
    start_value = count + shift
    variables = []
    for i in range(11):
        value = (start_value - i) % 39  # Der Modulo-Operator sorgt dafür, dass der Wert zwischen 0 und 38 bleibt
        variables.append(value)
    
    sun_rise(strip, variables)

def text_to_morse(text):
    morse_code = {
        'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.', 'G': '--.', 'H': '....',
        'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 'P': '.--.',
        'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
        'Y': '-.--', 'Z': '--..',
        '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-', '5': '.....', '6': '-....',
        '7': '--...', '8': '---..', '9': '----.',
        '.': '.-.-.-', ',': '--..--', '?': '..--..', '!': '-.-.--', ':': '---...', ';': '-.-.-.', '-': '-....-',
        '/': '-..-.', 'Ä': '.-.-', 'Ö': '--.', 'Ü': '..--'
    }

    morse_list = []
    for char in text:
        upper_char = char.upper()
        if upper_char in morse_code:
            morse_char = morse_code[upper_char]
            for c in morse_char:
                if c == '.':
                    morse_list.append(30)  # Punkt
                else:
                    morse_list.append(90)  # Strich
                morse_list.append(30) # Pause zwischen Punkten und Strichen
            morse_list.pop(-1)
            morse_list.append(120)  # Pause zwischen den Buchstaben
        elif upper_char == " ":
            morse_list.pop(-1)
            morse_list.append(350)  # Pause zwischen den Wörtern
    return morse_list


def printmorse(strip, code, u):
    morse_list = code
    print(u)
    print(morse_list[u])
    if u % 2 == 0:
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 165, 255))
        strip.show()
    else:
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()
    time.sleep(morse_list[u]/100)

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--clear', action='store_true', help='clear the display on exit')
args = parser.parse_args()

    # Create NeoPixel object with appropriate configuration.
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    # Intialize the library (must be called once before other functions).
strip.begin()


my_username = "LightClient"
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((IP, PORT))
client_socket.setblocking(False)

username = my_username.encode('utf-8')
username_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
client_socket.send(username_header + username)

message = None
commands = ["/stop", "/weiss", "/rot", "/orange", "/gelb", "/gruen", "/tuerkis", "/blau", "/violet"]
color_dict = {}
while True:
    print(f"Message: {message}")
    if sunpauseedit:
        if message == "/qsunpause":
            sunpauseedit = False
        else:
            if message.startswith('*s'):
                sun_start_time = datetime.strptime(message[2:], '%H:%M:%S').time()
                sunpauseedit = False
            elif message.startswith('*p'):
                sun_pause_time = datetime.strptime(message[2:], '%H:%M:%S').time()
                sunpauseedit = False
    if rainbowrun:
        rainbow(strip, x)
        if x >= 255:
            x = 0
        else:
            x += 1
    elif rainbowallrun:
        rainbowCycle(strip, w)
        if w >= 1280:
            w = 0
        else:
            w += 1
    elif morserun:
        printmorse(strip, morse_list, u)
        if u >= len(morse_list)-1:
            morserun = False
            u = 0
            colorWipe(strip, Color(0, 0, 0))
        else:
            u += 1
    elif rainbowCirclerun:
        if y == 0:
            circle(strip, Color(255, 0, 0))
        elif y == 1:
            circle(strip, Color(255, 100, 0))
        elif y == 2:
            circle(strip, Color(255, 255, 0))
        elif y == 3:
            circle(strip, Color(0, 255, 0))
        elif y == 4:
            circle(strip, Color(0, 255, 255))
        elif y == 5:
            circle(strip, Color(0, 0, 255))
        elif y == 6:
            circle(strip, Color(165, 0, 255))
        if y >= 6:
            y = 0
        else:
            y += 1
    elif nerdRun:
        nerd(strip, Color(0, 255, 0), z)
        z += 1
    elif sunRun:
        time_done = time_run() 
        count = int(time_done / 1107.6923)
        if count != countflanke:
            current_time = datetime.now().time()
            countflanke = count
            message = f"Count: {count}, Shift: {shift}, Time: {current_time}"
            message = message.encode('utf-8')
            message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
            client_socket.send(message_header + message)
        if datetime.now().time() >= sun_start_time and datetime.now().time() <= sun_pause_time:
            calculate_sun(strip, count, shift)
        else:
            colorWipe(strip, 0, 0)
        time.sleep(1)
    else:
        time.sleep(1)
        message = "restart"
        message = message.encode('utf-8')
        message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
        client_socket.send(message_header + message)
    
    try:
        while True:
            #receive things
            username_header = client_socket.recv(HEADER_LENGTH)
            if not len(username_header):
                print("Connection closed by the server")
                colorWipe(strip, Color(0, 0, 0))
                sys.exit()
            username_length = int(username_header.decode('utf-8').strip())
            username = client_socket.recv(username_length).decode('utf-8')

            message_header = client_socket.recv(HEADER_LENGTH)
            message_length = int(message_header.decode('utf-8').strip())
            message = client_socket.recv(message_length).decode('utf-8')
            print(f"{username} > {message}")

            
            if customcolor:
                if message == "q":
                    customcolor = False
                else:
                    try:
                        name, rgb_values = colorcustom(message.lower())
                        color_dict[name] = rgb_values
                        print(color_dict)
                        customcolor = False
                    except ValueError as e:
                        print(e)
            elif morsecode:
                if message == "q":
                    morsecode = False
                else:
                    morse_list = text_to_morse(message)
                    morserun = True
                    morsecode = False
            elif message == "/regenbogen":
                morserun = False
                rainbowallrun = False
                rainbowrun = True
                sunRun = False
                nerdRun = True
                rainbowCirclerun = False
                x = 0
            elif message == "/regenbogenkreis":
                morserun = False
                rainbowallrun = False
                rainbowrun = False
                sunRun = False
                nerdRun = True
                rainbowCirclerun = True
                y = 0
            elif message == "/regenbogen2":
                morserun = False
                rainbowallrun = True
                rainbowrun = False
                sunRun = False
                rainbowCirclerun = False
                nerdRun = False
                w = 0
            elif message == "/eigenefarbe":
                customcolor = True
            elif message == "/morsecode":
                u = 0
                rainbowrun = False
                sunRun = False
                rainbowCirclerun = False
                nerdRun = False
                rainbowallrun = False
                morsecode = True
                colorWipe(strip, Color(0, 0, 0))
            elif message == "/nerd":
                morserun = False
                rainbowallrun = False
                rainbowrun = False
                rainbowCirclerun = False
                sunRun = False
                nerdRun = True
                z = 0
            elif message == "/sun":
                colorWipe(strip, Color(0, 0, 0), 0)
                morserun = False
                rainbowallrun = False
                nerdRun = False
                rainbowrun = False
                rainbowCirclerun = False
                sunRun = True
            elif message == "/sunpause":
                sunpauseedit = True
            elif message == "/weiss":
                colorWipe(strip, Color(255, 255, 255))
            elif message == "/rot":
                colorWipe(strip, Color(255, 0, 0))   
            elif message == "/orange":
                colorWipe(strip, Color(255, 100, 0))       
            elif message == "/gelb":
                colorWipe(strip, Color(255, 255, 0))       
            elif message == "/gruen":
                colorWipe(strip, Color(0, 255, 0))      
            elif message == "/tuerkis":
                colorWipe(strip, Color(0, 255, 255))
            elif message == "/blau":
                colorWipe(strip, Color(0, 0, 255))
            elif message == "/violet":
                colorWipe(strip, Color(165, 0, 255))
            elif message == "/stop":
                colorWipe(strip, Color(0, 0, 0))
            elif message == "/shutdown":
                print("shutdown")
                colorWipe(strip, Color(0, 0, 0))
                call("sudo halt", shell=True)
            elif message == "/quit":
                print("quit")
                colorWipe(strip, Color(0, 0, 0))
                sys.exit()
            elif message == 'shiftplus':
                shift += 1
            elif message == 'shiftminus':
                shift -= 1
            elif message.startswith('/'):
                if message[1:] in color_dict.keys():
                    print(message)
                    print(f"Farbe: {color_dict[message[1:]]}")
                    colorWipe(strip, Color(color_dict[message[1:]][0], color_dict[message[1:]][1], color_dict[message[1:]][2]))
            if message in commands or message[1:] in color_dict.keys():
                morserun = False
                rainbowrun = False
                sunRun = False
                rainbowCirclerun = False
                nerdRun = False
                rainbowallrun = False
    except IOError as e:
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
              print('Reading error',str(e))
              colorWipe(strip, Color(0, 0, 0))
              sys.exit()
        continue

    except Exception as e:
        print('General error', str(e))
        colorWipe(strip, Color(0, 0, 0))
        sys.exit()
    
