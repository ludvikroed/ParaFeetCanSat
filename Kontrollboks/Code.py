import board
import busio
import digitalio
import analogio
import adafruit_rfm9x
import time
import json

# SPI for SD card and radio
spi = busio.SPI(board.SCK, MOSI=board.MOSI, MISO=board.MISO)

# Radio parameters
RADIO_FREQ_MHZ = 869.4
CS = digitalio.DigitalInOut(board.RFM_CS)
RESET = digitalio.DigitalInOut(board.RFM_RST)

# UART for sending data to Arduino and PC
uart = busio.UART(board.TX, board.RX, baudrate=9600)

# Initialize RFM radio for transmitter and receiver
transmitter_rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)
transmitter_rfm9x.tx_power = 23
receiver_rfm9x = adafruit_rfm9x.RFM9x(spi, CS, RESET, RADIO_FREQ_MHZ)
receiver_rfm9x.tx_power = 23

# LED control
led_pins = [board.D5, board.D9, board.D10, board.D11, board.D6, board.D12]
leds = [digitalio.DigitalInOut(pin) for pin in led_pins]
for led in leds:
    led.direction = digitalio.Direction.OUTPUT

# Switches and button setup
switch_pins = [board.A0, board.A1, board.A2]
button_pin = board.A3
button_analog = analogio.AnalogIn(button_pin)
switches = [analogio.AnalogIn(pin) for pin in switch_pins]

data_to_send = "Slipp"
last_button_press = 0
last_data_sent_to_arduino = 0
variable_to_send = 0
altitude = None
last_switch_1 = False
inAir = False

while True:
    data_to_pc = [{}]
    data_to_pc[0]["error"] = []
    button_value = button_analog.value
    switch_values = [switch.value for switch in switches]
    print(switch_values, button_value)
    button_pressed = button_value > 45_000
    switch_1 = switch_values[0] > 40_000
    switch_2 = switch_values[1] > 30_000
    switch_3 = switch_values[2] > 30_000

    data_to_pc[0]["switches"] = [switch_1, switch_2, switch_3]
    data_to_pc[0]["button"] = button_pressed

    if switch_2:
        if last_data_sent_to_arduino + 1 < time.monotonic():
            message = f"{variable_to_send}\n"
            uart.write(message.encode())
            data_to_pc[0]["arduino"] = message
            last_data_sent_to_arduino = time.monotonic()

        packet = receiver_rfm9x.receive()
        if packet is not None:
            leds[3].value = True
            try:
                packet_str = packet.decode("utf-8")
                received_data = json.loads(packet_str)
                data_to_pc.append(received_data)

                if '10' in received_data and received_data['10']:
                    leds[2].value = True
                else:
                    leds[2].value = False

                if '5' in received_data:
                    try:
                        pressure = int(received_data['5'])
                    except ValueError:
                        data_to_pc[0]["error"].append("pressure conversion error")

                if '4' in received_data:
                    try:
                        altitude = int(received_data['4'])
                        variable_to_send = altitude
                        leds[1].value = not (-10 < altitude < 1100)
                    except ValueError:
                        data_to_pc[0]["error"].append("altitude conversion error")
                        leds[1].value = True

                if '2' in received_data:
                    try:
                        data_mottat_av_cansat = received_data['2']
                        print(data_mottat_av_cansat)
                        if data_mottat_av_cansat == True:
                            leds[4].value = True
                        else:
                            leds[4].value = False
                    except ValueError:
                        data_to_pc[0]["error"].append("feil med mottat data for CanSat")
                        leds[4].value = False

                inAir = received_data.get('14', False)
            except (KeyError, ValueError, json.JSONDecodeError) as e:
                data_to_pc[0]["error"].append(f"Data processing error: {e}")
        else:
            leds[3].value = False

        if switch_3 and button_pressed:
            print("her")
            if last_button_press + 2 < time.monotonic():
                last_button_press = time.monotonic()
                if data_to_send == "Slipp":
                    data_to_send = "Ikke slipp"
                    leds[0].value = False
                else:
                    data_to_send = "Slipp"
                    leds[0].value = True

        if altitude is None:
            leds[5].value = True
        elif inAir and altitude < 110:
            leds[5].value = False
        else:
            leds[5].value = True

        transmitter_rfm9x.send(data_to_send.encode())
        data_to_pc[0]["sent"] = data_to_send
    else:
        if not switch_1:
            for led in leds:
                led.value = False
    if switch_1:
        last_switch_1 = True
        for led in leds:
            led.value = True
    else:
        if last_switch_1:
            for led in leds:
                led.value = False
            last_switch_1 = False
    print(data_to_pc)
