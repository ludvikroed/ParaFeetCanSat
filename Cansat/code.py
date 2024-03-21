# Vi impoterer alle bibliotekene vi trenger
import os
import busio #brukt for å lage SPI og UART kominikasjonsprotokoller
import board #brukt for å få tilgang til pin-er og funksjoner på kretskortet
import pwmio #brukt for å styre servo
import digitalio #brukt for å lese digital input
import analogio #brukt for å lese analog input

import time #brukt for timing
import json #brukt for å komprimere data og gjøre om til bytes og omvendt
import math #brykt for å gjøre mer avansert matte

import adafruit_rfm9x #bibliotek til radio
import adafruit_dps310 # bibliotek til trykk og tempratur sensor
import adafruit_gps # bibliotek til GPS
import adafruit_sdcard # bibliotek til SD kort
import storage # brukt for å lagre ting på SDkortet
from adafruit_motor import servo # vi bruker innebygde servo funksjoner fra adafruit sitt "motor bibliotek"
from adafruit_lsm6ds.lsm6ds3 import LSM6DS3 # bibliotek til gyroskop og akselrometer

spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)#spi. kominikasjonsprotokoll for sd-kortet og radioen
uart = busio.UART(board.TX, board.RX, baudrate=9600)#kominikasjonsprotokoll for å sende meldinger fra pc til adafruit via ledning
i2c = board.I2C()  # uses board.SCL and board.SDA
cs = digitalio.DigitalInOut(board.D10)

def init_sd_card(): #initialiserer SD kortet
    sdcard = adafruit_sdcard.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")
def init_gps():#initialiserer GPS-en
    gps = adafruit_gps.GPS_GtopI2C(i2c, debug=False)  # Use I2C interface # Initialize GPS module
    gps.send_command(b"PMTK314,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0")# Turn on everything in the GPS module
    gps.send_command(b"PMTK220,1000")# Set update rate to once a second (1hz)
    return gps
def init_dps310():#initialiserer trykk og tempratur sensor
    return adafruit_dps310.DPS310(i2c)
def init_LSM6DS3():#initialiserer akselrometeret og gyroskopet
    return LSM6DS3(i2c)
def init_radio():#initialiserer radioen
    # Define radio parameters
    RADIO_FREQ_MHZ = 869.4  # Frequency of the radio in Mhz. Must match your module! Can be a value like 915.0, 433.0, etc.
    # Define pins connected to the RFM9x chip
    CS = digitalio.DigitalInOut(board.RFM_CS)
    RESET = digitalio.DigitalInOut(board.RFM_RST)
    # Initialize RFM radio for transmitter
    transmitter_rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)
    transmitter_rfm9x.tx_power = 23  # Set transmit power
    # Initialize RFM radio for receiver
    receiver_rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)
    receiver_rfm9x.tx_power = 23  # Set transmit power
    return [transmitter_rfm9x, receiver_rfm9x]
def init_servo():#initialiserer servoen
    pwm = pwmio.PWMOut(board.D25, duty_cycle=2 ** 15, frequency=50)# Set up PWM output for the servo
    my_servo = servo.Servo(pwm)
    return my_servo
#under lager jeg en "dictionary" med statusen av alle sensorene og funksjonene for å aktivere disse. hvis en av sensorene feiler vil de blir forsøkt å bli aktivert igjen.
alle_sensorer_status = {"sd_card": [init_sd_card, False],
                        "gps": [init_gps, False],
                        "dps310": [init_dps310, False],
                        "gyro": [init_LSM6DS3, False],
                        "radio": [init_radio, False],
                        "servo": [init_servo, False],
                        }
# på de 37 linjene under blir alle komponentene forsøkt initialisert. hvis det skjer noe feil vil dette bli lagret i orboka og de vil bli forsøkt initialisert flere ganger når while True løkka kjører
try:
    init_sd_card()
    alle_sensorer_status["sd_card"][1] = True
except Exception as e:
    print("SD Card Initialization Error:", e)
    alle_sensorer_status["sd_card"][1] = False
try:
    gps = init_gps()
    alle_sensorer_status["gps"][1] = True
except Exception as e:
    print("gps Initialization Error:", e)
    alle_sensorer_status["gps"][1] = False
try:
    dps310 = init_dps310()
    alle_sensorer_status["dps310"][1] = True
except Exception as e:
    print("dps310 Initialization Error:", e)
    alle_sensorer_status["dps310"][1] = False
try:
    gyro_sensor = init_LSM6DS3()
    alle_sensorer_status["gyro"][1] = True
except Exception as e:
    print("lsm6ds3 Initialization Error:", e)
    alle_sensorer_status["gyro"][1] = False
try:
    radio = init_radio() #transmitter_rfm9x, receiver_rfm9x
    transmitter_rfm9x = radio[0]
    receiver_rfm9x = radio[1]
    alle_sensorer_status["radio"][1] = True
except Exception as e:
    print("radio Initialization Error:", e)
    alle_sensorer_status["radio"][1] = False
try:
    my_servo = init_servo()
    alle_sensorer_status["servo"][1] = True
except Exception as e:
    print("servo Initialization Error:", e)
    alle_sensorer_status["servo"][1] = False

print(alle_sensorer_status)

# under tar vi start trykk for å regne ut høyde til vår CanSat
try:
    start_pressure = dps310.pressure
    start_pressure_error = False
except:
    start_pressure = 1000 #sett ca trykk på oppskytnignsdag
    start_pressure_error = True
# måler analog input på pin A1 dette er fordi at hvis koppen er tilkoblet vil en lednign koble 3,3 volt til A1. Dette gjør at vi kan se om koppen og den andre fallskjermen er
analog_input = analogio.AnalogIn(board.A1)

last_sent_radio_data = time.monotonic()
data_list = {}
gps_data = {}
data_list_radio = {}
gps_data_to_send = {}
counter_radio = 0
counter_loop = 0
slipp_2_fallskjerm = 70 # Setter høyden den andre fallskjremen skal slippes hvis den ikke får besked tidligere om å slippe den andre fallskjrmen
can_sat_in_air = False
drop_2_parachute = False
altitude = 0
last_servo_angel = 90
received_data = False
sendetid_prosent = 0

print("-----------Starting loop----------")
while True:
    error_messages = {}
    packet = receiver_rfm9x.receive() # her mottar vi data fra ground station.
    time_packet = time.monotonic()

    # for løkka under gjennom gjennom ordboka som lagrer statusen til alle sensorene. Hvis statusen er False vil den forsøke å initialisere sensoren på nytt.
    for sensor, [init_func, status] in alle_sensorer_status.items():
        if not status:
            try:
                init_func()  # Prøver å initialisere sensoren
                alle_sensorer_status[sensor][1] = True  # Oppdaterer status til True hvis ingen feil oppstår
                print(f"{sensor} initialisert suksessfullt.")
            except Exception as e:
                print(f"Feil ved initialisering av {sensor}: {e}")
    # Hvis verdien på analog input er mindre enn 30 000 er koppen ikke tilkoblet.
    #Hvis verdien er større betyr det at koppen er tilkoblet vil verdien være over 60 000
    kopp_connected = analog_input.value > 30000

    if packet is not None: # Skjekker om vi har mottat noe data
        try:
            # Decode the received packet as a UTF-8 string
            packet_text = packet.decode("utf-8")
            print("Received:", packet_text)
            received_data = True
        except UnicodeDecodeError:
            received_data = False
            packet_text = "failed decoding radio message"
            error_messages.radio_in = "Received packet cannot be decoded as UTF-8."
    else:
        time_now = time.monotonic()
        if (time_packet + 2) < time_now:
            received_data = False
        else:
            received_data = True
        packet_text = False
    last_radio_message = {"data": packet_text, "time": time_packet}
    print(received_data)
    #skjekk om vi har lette fra bakken:

    # Can sat in air vil være True hvis CanSat-en har vært 20 meter over høyden vi skal slippe fallskjermen på. neste gang den passerer under høyden vi skal slippe fallskjermen på vet den at vi skal slippe fallskjermen
    if slipp_2_fallskjerm + 20  < altitude:
        can_sat_in_air = True

    # Hvis CanSat in air er True og vi er under siste høyde for slipp av andre fallskjerm
    if can_sat_in_air and altitude < slipp_2_fallskjerm:
        drop_2_parachute = True
    if packet_text == "Slipp": # Hvis vi mottar slipp slipper vi andre fallskjerm
        drop_2_parachute = True
    if packet_text == "Ikke slipp": # Hvis vi mottar ikke slipp slipper vi ikke andre fallskjerm
        drop_2_parachute = False
    if drop_2_parachute:
        if kopp_connected:
            if last_servo_angel == 0:
                my_servo.angle = 90
                last_servo_angel = 90
            else:
                my_servo.angle = 0
                last_servo_angel = 0
        else:
            my_servo.angle = 0
    else:
        my_servo.angle = 90

    # Transmit radio data at a regular interval
    if time.monotonic() > (last_sent_radio_data + 1):
        try:
            # Leser data fra trykksensoren. Vi gjør dette alene fordi trykket er veldig viktig for oss for at vi skal kunne vite hvor høyt vår CanSat er over bakken
            pressure = dps310.pressure
        except:
            error_messages["pressure"] = "pressure failed"
            pressure = 0
        try:
            #leser data fra resten av sensorene
            temperature = dps310.temperature
            acceleration = gyro_sensor.acceleration
            gyro = gyro_sensor.gyro
        except:
            error_messages["Sensors"] = "temperature, acceleration, gyro failed"
            print("----feil----")
            temperature, acceleration, gyro = None, None, None

        time_now = time.monotonic()
        # under regner vi ut høyden cansat-en er over bakken:
        altitude = 8500 * math.log(start_pressure / pressure)
        """
        Vi lager en liste med data som heter data list og en som heter data list radio.
        Det er fordi vi kan ikke sende så mye data via radio-en.
        Vi lagrer masse data på SD kortet også sender vi bare den absulutt nødvendige data-en via radio ned til bakken
        """
        # legger til Call sign så det er lett å se at det er vår data
        data_list["c_s"] = "Para Feet"
        try:
            data_list["gps_fix"] = gps.has_fix
        except:
            data_list["gps_error"] = "no gps connected"
        data_list["gps"] = gps_data
        data_list["a"] = altitude
        data_list["p"] = pressure
        data_list["temp"] = temperature
        data_list["accel"] = acceleration
        data_list["gyro"] = gyro
        data_list["error"] = error_messages
        data_list["r_received"] = last_radio_message
        data_list["in_air"] = can_sat_in_air
        data_list["2_parachute"] = drop_2_parachute
        data_list["s_angel"] = my_servo.angle
        data_list["count_R"] = counter_radio
        data_list["count_L"] = counter_loop
        data_list["t_now"] = time_now
        radio_interval = time_now - last_sent_radio_data
        data_list["r_interval"] = radio_interval
        data_list["kopp"] = kopp_connected
        data_list["sendetid"] = sendetid_prosent
        data_list_str = str(data_list)
        try:
            # Open a file in append mode ("/sd/text.txt" is the file path)
            with open("/sd/text.txt", "a") as file:
                # Append new data to the file
                file.write(data_list_str)
                file.write("\n")  # Legg til en ny linje for hver oppføring
        except:
            data_list_radio[13] = False
            pass
        data_list_radio[0] = "Para Feet"
        try:
            data_list_radio[11] = gps.has_fix
        except:
            data_list_radio[12] = "no gps connected"
        # {0: call sign, 1: akselrometer, 2: received_data, 3: gps ,4: altitude ,5: trykk ,6: tempratur,7: counter_radio,8: tid når radio ble sent, 9: slippes den andre fallskjrmen ,10:er koppen tilkoblet?, 11: gps_fix, 12: gps error, 13: hvis false. data er ikke lagret på sd kort}
        data_list_radio[1] = acceleration
        data_list_radio[2] = received_data
        data_list_radio[3] = gps_data_to_send
        data_list_radio[4] = altitude
        data_list_radio[5] = pressure
        data_list_radio[6] = temperature
        data_list_radio[7] = counter_radio
        data_list_radio[8] = time.monotonic()
        data_list_radio[9] = drop_2_parachute
        data_list_radio[10] = kopp_connected

        # Convert data to JSON-formatted string and then encode to bytes
        data_bytes = bytes(json.dumps(data_list_radio), "utf-8")
        try:
            #sender data via radio
            print(time.monotonic())
            time_start_radio = time.monotonic()
            transmitter_rfm9x.send(data_bytes)
            sendetid = time.monotonic() - time_start_radio
            sendetid_prosent = radio_interval / sendetid
        except Exception as transmit_error:
            print("Transmission failed. Error:", str(transmit_error))
        #resetter alle listene med data
        data_list = {}
        data_list_radio = {}
        counter_radio += 1
        last_sent_radio_data = time.monotonic()
    counter_loop += 1

    # Update GPS data
    try:
        if not gps.update() or not gps.has_fix:
            continue
    except:
        continue
    try:
        # Heter data fra GPS. Hvis gps-en får en error prøver den nederst å hente så lite data som mulig.
        if gps.nmea_sentence[3:6] == "GSA":
            gps_data_to_send = {"lat, long": [gps.latitude, gps.longitude], "a": gps.altitude_m}
            gps_data = {"gps_time": time.monotonic(), "lat, long": [gps.latitude, gps.longitude], "a": gps.altitude_m, "2d_fix": gps.has_fix, "3d_fix": gps.has_3d_fix, "signal": {"pdop": gps.pdop, "hdop": gps.hdop, "vdop": gps.vdop}}
        elif gps.has_fix:
            gps_data_to_send = {"lat, long": [gps.latitude, gps.longitude], "a": gps.altitude_m}
            gps_data = {"gps_time": time.monotonic(), "lat, long": [gps.latitude, gps.longitude], "a": gps.altitude_m, "2d_fix": gps.has_fix, "3d_fix": gps.has_3d_fix, "signal": {"pdop": gps.pdop, "hdop": gps.hdop, "vdop": gps.vdop}}
    except:
        try:
            gps_data_to_send = {"lat, long": [gps.latitude, gps.longitude]}
            gps_data = {"lat, long": [gps.latitude, gps.longitude]}
        except:
            gps_data_to_send = {"error": "no gps data"}
            error_messages["GPS"] = ["gps failed", time.monotonic()]
