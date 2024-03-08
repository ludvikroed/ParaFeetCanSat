# Write your code here :-)
import os
import busio
import board
import pwmio
import digitalio
import analogio

import time
import json
import math

import adafruit_rfm9x
import adafruit_dps310
import adafruit_gps
import adafruit_sdcard
import storage
from adafruit_motor import servo
from adafruit_lsm6ds.lsm6ds3 import LSM6DS3

spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)#spi. kominikasjonsprotokoll for sd-kortet og radioen
uart = busio.UART(board.TX, board.RX, baudrate=9600)#kominikasjonsprotokoll for å sende meldinger fra pc til adafruit via ledning
i2c = board.I2C()  # uses board.SCL and board.SDA

def init_sd_card():# sd card:
    cs = digitalio.DigitalInOut(board.D10)
    sdcard = adafruit_sdcard.SDCard(spi, cs)
    vfs = storage.VfsFat(sdcard)
    storage.mount(vfs, "/sd")
def init_gps():
    gps = adafruit_gps.GPS_GtopI2C(i2c, debug=False)  # Use I2C interface # Initialize GPS module
    gps.send_command(b"PMTK314,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0")# Turn on everything in the GPS module
    gps.send_command(b"PMTK220,1000")# Set update rate to once a second (1hz)
    return gps
def init_dps310():
    return adafruit_dps310.DPS310(i2c)# Create DPS310 instance for barometric pressure and temperature
def init_LSM6DS3():
    return LSM6DS3(i2c)# Create LSM6DS3 instance for accelerometer and gyro sensor
def init_radio():
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
def init_servo():
    pwm = pwmio.PWMOut(board.D25, duty_cycle=2 ** 15, frequency=50)# Set up PWM output for the servo
    my_servo = servo.Servo(pwm)
    return my_servo

alle_sensorer_status = {"sd_card": [init_sd_card, False],
                        "gps": [init_gps, False],
                        "dps310": [init_dps310, False],
                        "gyro": [init_LSM6DS3, False],
                        "radio": [init_radio, False],
                        "servo": [init_servo, False],
                        }
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
    sensor = init_LSM6DS3()
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

try:
    start_pressure = dps310.pressure
    start_pressure_error = False
except:
    start_pressure = 1000 #sett ca trykk på oppskytnignsdag
    start_pressure_error = True

analog_input = analogio.AnalogIn(board.A1)

last_sent_radio_data = time.monotonic()
data_list = {}
gps_data = {}
data_list_radio = {}
gps_data_to_send = {}
counter_radio = 0
counter_loop = 0
slipp_2_fallskjerm = 100
can_sat_in_air = False
drop_2_parachute = False
altitude = 0
last_servo_angel = 90

print("-----------Starting loop----------")
while True:
    error_messages = {}
    packet = receiver_rfm9x.receive()
    time_packet = time.monotonic()

    for sensor, [init_func, status] in alle_sensorer_status.items():
        if not status:
            try:
                init_func()  # Prøver å initialisere sensoren
                alle_sensorer_status[sensor][1] = True  # Oppdaterer status til True hvis ingen feil oppstår
                print(f"{sensor} initialisert suksessfullt.")
            except Exception as e:
                print(f"Feil ved initialisering av {sensor}: {e}")
    kopp_connected = analog_input.value > 30000
    # Process received radio packet
    if packet is not None:
        try:
            # Decode the received packet as a UTF-8 string
            packet_text = packet.decode("utf-8")
            print("Received:", packet_text)
        except UnicodeDecodeError:
            packet_text = "failed decoding radio message"
            error_messages.radio_in = "Received packet cannot be decoded as UTF-8."
    else:
        packet_text = False
    last_radio_message = {"data": packet_text, "time": time_packet}

    #skjekk om vi har lette fra bakken:
    print(slipp_2_fallskjerm, can_sat_in_air, altitude)
    if slipp_2_fallskjerm * 2 < altitude:
        can_sat_in_air = True
    #skjekk om vi skal slippe den andre fallskjermen
    if can_sat_in_air and altitude < slipp_2_fallskjerm:
        drop_2_parachute = True
    if packet_text == "slipp":
        drop_2_parachute = True
    if packet_text == "Ikke slipp":
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
    if time.monotonic() > (last_sent_radio_data + 0.5):
        try:
            # Read additional sensor data
            pressure = dps310.pressure
        except:
            error_messages.pressure = "pressure failed"
            pressure = 0
        try:
            temperature = dps310.temperature
            acceleration = sensor.acceleration
            gyro = sensor.gyro
        except:
            error_messages["Sensors"] = "temperature, acceleration, gyro failed"
            temperature, acceleration, gyro = None, None, None

        time_now = time.monotonic()
        # Calculate altitude from pressure
        altitude = 8500 * math.log(start_pressure / pressure)
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
        data_list["r_interval"] = time_now - last_sent_radio_data
        data_list["kopp"] = kopp_connected

        try:
            # Open a file in append mode ("/sd/text.txt" is the file path)
            with open("/sd/text.json", "a") as json_file:
                # Append new data to the file
                json.dump(data_list, json_file)
                json_file.write("\n")  # Add a newline for each entry
        except:
            data_list_radio["d_s"] = False
            pass

        data_list_radio["c_s"] = "Para Feet"
        try:
            data_list_radio["gps_fix"] = gps.has_fix
        except:
            data_list_radio["gps_error"] = "no gps connected"
        data_list_radio["gps"] = gps_data_to_send
        data_list_radio["a"] = altitude
        data_list_radio["p"] = pressure
        data_list_radio["temp"] = temperature
        data_list_radio["count_R"] = counter_radio
        data_list_radio["t_now"] = time.monotonic()
        data_list_radio["in_air"] = can_sat_in_air
        data_list_radio["2_parachute"] = drop_2_parachute
        data_list_radio["kopp"] = kopp_connected

        #print(data_list_radio)

        #print("trying to send:", data_list_radio)
        # Convert data to JSON-formatted string and then encode to bytes
        data_bytes = bytes(json.dumps(data_list_radio), "utf-8")

        try:
            transmitter_rfm9x.send(data_bytes)
            #print("Transmission successful.")
        except Exception as transmit_error:
            print("Transmission failed. Error:", str(transmit_error))

        data_list = {}
        data_list_radio = {}
        counter_radio += 1
        last_sent_radio_data = time.monotonic()
    counter_loop += 1
    # Update GPS data
    try:
        print("gps fix", gps.has_fix)
        if not gps.update() or not gps.has_fix:
            continue
    except:
        continue

    try:
        # Process GPS data
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
