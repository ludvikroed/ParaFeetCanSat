"""
En pc er koblet til adafruit-en som mottar data via den innebygde radio-en. 
vi bruker Serial monitor som mottar data og putter data-en inn i en text fil
Denne koden leser kontinuele denne text filen. Når filen blir oppdatert vil den plåtte ett nytt punkt på grafen.
"""

import ast
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
 
# Globale variabler for å holde styr på dataene og filens tilstand
a_values = []  # Liste for å holde verdiene av "a"
t_now_values = []  # Liste for å holde tidspunktene for hver "a" verdi
last_read_line = 0  # Holder styr på hvor mange linjer som har blitt lest
# {0: call sign, 1: akselrometer, 2: gyroskop, 3: gps ,4: altitude ,5: trykk ,6: tempratur,7: counter_radio,8: tid når radio ble sent, 9: slippes den andre fallskjrmen ,10:er koppen tilkoblet?, 11: gps_fix, 12: gps error, 13: hvis false. data er ikke lagret på sd kort, 14 in air}

try:
    def update_graph(frame):
        global last_read_line
        global a_values
        global t_now_values
        new_data = False  # Flag for å sjekke om ny data ble lagt til
    
        try:
            # Åpner filen i 'r' modus og leser nye linjer
            with open(filbane, "r", encoding='utf-8') as file:
                lines = file.readlines()[last_read_line:]  # Les kun nye linjer
    
            for line in lines:
                try:
                    data = ast.literal_eval(line.strip())
                    høyde = data[1][4]
                    tid = data[1][8]
                    a_values.append(høyde)
                    t_now_values.append(tid)
                    new_data = True
                except (ValueError, SyntaxError) as e:
                    print(f"Feil ved behandling av linjen: {e}")
    
            if new_data:
                # Oppdater grafen kun hvis det er nye data
                plt.cla()  # Fjern tidligere tegnede linjer
                plt.plot(t_now_values, a_values, label='Verdi av a') # plotter ny graf med nye tall
                plt.title("Høyde")
                plt.legend(loc="upper left")
                #setter navn på grafer
                plt.xlabel("Tid (sekunder)")
                plt.ylabel("Meter")
                plt.draw()#tegner grafen
            while True:
                #Denne løkka fjerner data så vi altid har data fra de 200 siste sekundene dette gjør at vi ikke har masse unødvendig data
                siste_tid = t_now_values[-1]
                første_tid = t_now_values[0]
                if siste_tid - første_tid > 200:
                    t_now_values.pop(0)
                    a_values.pop(0)
                else:
                    break
            last_read_line += len(lines)  # Oppdater antall leste linjer
        except Exception as e:
            print(f"En feil oppsto ved oppdatering av grafen: {e}")
except (ValueError, SyntaxError) as e:
    print("feil med funksjon: ", e)
# Sett opp plottet
plt.title("Verdier av 'a' Over Tid")
 
# Angi banen til din kontinuerlig oppdaterte fil her
filbane = "devttyusbmodem101_2024_02_26.11.05.11.826.txt"
 
# Opprett animasjonen som oppdaterer grafen hvert halve sekund (500 ms)
ani = FuncAnimation(plt.gcf(), update_graph, interval=500)
 
plt.show()
 
