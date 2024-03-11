
import board
import busio
import digitalio
import analogio
import adafruit_rfm9x
import time
import json

# ---- brytere ---
# ---- 0 ------------- 1 -------2----------3----
# ikke tilkoblet -- lys test - alt på---knapp på

# ------------lys---------
# 1------2------------------------3---------------------4----
# ------------------------------------- -------------------------------5--------6
# trykk bra- trykk dorlig - lyser når vi får data --kopp tilkoblet---slipp---ikke slipp

# SPI-kommunikasjonsprotokoll for SD-kortet og radioen
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Definer radio parametere
RADIO_FREQ_MHZ = 869.4
CS = digitalio.DigitalInOut(board.RFM_CS)
RESET = digitalio.DigitalInOut(board.RFM_RST)

# Define the UART connection for å sende data adafruit til arduino og pc
uart = busio.UART(board.TX, board.RX, baudrate=9600)

# Initialiser RFM radio for mottaker, Initialiser RFM radio for sender
transmitter_rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)
transmitter_rfm9x.tx_power = 23
receiver_rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)
receiver_rfm9x.tx_power = 23

# fra venstre lys 0 i liste = 0, 1 i liste = 2, 2 i liste = 3, 3 i liste = 4, 4 i liste = 5, 5 i liste = 6
lys_control_box = [board.D5, board.D9, board.D10, board.D11, board.D6, board.D12]
leds = [digitalio.DigitalInOut(pin) for pin in lys_control_box]
for led in leds:
    led.direction = digitalio.Direction.OUTPUT

switch_pins = [board.A0, board.A1, board.A2]
knapp_pin = board.A3
knapp_analog = analogio.AnalogIn(knapp_pin)
switches = [analogio.AnalogIn(pin) for pin in switch_pins]

data_to_send = "Slipp"
siste_trykk = 0
siste_sent_data_arduino = 0
variable_to_send = 0
altitude = None
last_bryter_1 = False
inAir = False

while True:
    data_to_pc =[{}]
    data_to_pc[0]["error"] = []
    knapp_value = knapp_analog.value
    switch_values = [switch.value for switch in switches]

    knapp = knapp_value > 30000
    bryter_1 = switch_values[0] > 30000
    bryter_2 = switch_values[1] > 30000
    bryter_3 = switch_values[2] > 50000

    data_to_pc[0]["brytere"] = [bryter_1, bryter_2, bryter_3]
    data_to_pc[0]["knapp"] = knapp
    #print(switch_values[0], switch_values[1], switch_values[2], knapp_value)
    #print(bryter_1, bryter_2, bryter_3, knapp)

    if bryter_2:
        if siste_sent_data_arduino + 1 < time.monotonic():
            message = (
                str(variable_to_send) + "\n"
            )  # Convert the variable to string and add newline
            uart.write(message.encode())
            #print("sent:", message, "to arduino")
            data_to_pc[0]["arduino"] = message
            siste_sent_data_arduino = time.monotonic()

        # Motta data over radioen
        packet = receiver_rfm9x.receive()
        #print(packet)

        #print("received: ", packet)
        # Sender data via Serial til arduino og pc
        # uart.write(packet)
        if packet is not None:
            leds[3].value = True
            try:
                try:
                    packet_str = str(packet, "utf-8")
                except:
                    data_to_pc[0]["error"].append("packet_str error")
                received_data = json.loads(packet_str)
                print("Received data:", received_data)
                data_to_pc.append(received_data)
                if received_data['10'] == True:
                    leds[2].value = True
                else:
                    leds[2].value = False
                try:
                    pressure = int(received_data['5'])
                except:
                    data_to_pc[0]["erorr"].append("pressure error")
                    #print("----------------pressure error----------------")
                try:
                    altitude = int(received_data['4'])
                    variable_to_send = altitude
                    if -10 < altitude < 1100:
                        leds[0].value = True
                        leds[1].value = False
                    else:
                        leds[1].value = True
                        leds[0].value = False

                except:
                    data_to_pc[0]["erorr"].append("altitude error")
                    leds[1].value = True
                    leds[0].value = False
                try:
                    inAir = received_data['14']
                except:
                    data_to_pc[0]["erorr"].append("error with can sat in air")
            except KeyError as error:
                data_to_pc[0]["erorr"].append(error)
        else:
            leds[3].value = False
        if bryter_3:
            if knapp:
                if siste_trykk + 2 < time.monotonic():
                    siste_trykk = time.monotonic()
                    if data_to_send == "Ikke slipp":
                        data_to_send = "slipp"
                    else:
                        data_to_send = "Ikke slipp"
            if altitude == None:
                leds[4].value = False
                leds[5].value = True
            elif inAir and (altitude < 110):
                leds[4].value = True
                leds[5].value = False
            else:
                leds[4].value = False
                leds[5].value = True
            # Send data over radioen
        transmitter_rfm9x.send(bytes(data_to_send, "utf-8"))
        #print("Data sent:", data_to_send)
        data_to_pc[0]["sent"] = data_to_send
    else:
        if bryter_1 == False:
            for led in leds:
                led.value = False
    if bryter_1:
        last_bryter_1 = True
        for led in leds:
            led.value = True

    else:
        if last_bryter_1:
            for led in leds:
                led.value = False
            last_bryter_1 = False
    print(data_to_pc)
