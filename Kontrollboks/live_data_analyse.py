"""
En pc er koblet til adafruit-en som mottar data via den innebygde radio-en. 
vi bruker Serial monitor som mottar data og putter data-en inn i en text fil
Denne koden leser kontinuele denne text filen. Når filen blir oppdatert vil den plåtte ett nytt punkt på grafen så vi kontinuelig ser høyden til vår CanSat.
"""

import ast  # Importerer ast for å trygt evaluere strenger som Python-kode
import matplotlib.pyplot as plt  # Importerer matplotlib for plotting
from matplotlib.animation import FuncAnimation  # For å animere grafen
 
# Globale variabler for å holde styr på dataene
a_values = []  # Liste for å holde høydeverdier
t_now_values = []  # Liste for å holde tidspunktene for hver høydeverdi
last_file_pos = 0  # Holder styr på siste posisjon i filen for å lese kun nye data
 
filbane = "COM3_2024_03_12.14.35.16.001.txt"# Navnen til text filen som skal analyseres
 
def update_graph(frame):
    global a_values, t_now_values, last_file_pos  # Bruker globale variabler inni funksjonen
 
    try:
        # Åpner filen for lesing og hopper til siste kjente posisjon for å lese nye data
        with open(filbane, "r", encoding='utf-8') as file:
            file.seek(last_file_pos)  # Går til siste leseposisjon
            lines = file.readlines()  # Leser kun nye linjer fra filen
            last_file_pos = file.tell()  # Oppdaterer leseposisjonen for neste kall
 
        # Behandler hver linje som er lest fra filen
        for line in lines:
            try:
                # Evaluerer linjen trygt som en Python-uttrykk og sjekker dens lengde
                data = ast.literal_eval(line.strip())
                if len(data) > 1:
                    data_from_air = data[1]
                    # Sjekker om nøkkel '4' (høyde) og '8' (tid) finnes i dataen
                    if "4" in data_from_air and "8" in data_from_air:
                        høyde = data_from_air["4"]
                        tid = data_from_air["8"]
                        # Legger til høyde og tid i deres respektive lister
                        a_values.append(float(høyde))
                        t_now_values.append(float(tid))
            except:
                print("Feil med denne linjen", data)
 
        # Fjerner data som er eldre enn 200 sekunder for å vise kun de siste 200 sekundene
        while t_now_values and (t_now_values[-1] - t_now_values[0] > 200):
            t_now_values.pop(0)
            a_values.pop(0)
        # Tegner grafen på nytt med oppdaterte data hvis det er nye data
        plt.cla()  # Fjerner tidligere grafer
        plt.plot(t_now_values, a_values, label='Høyde over tid') # Tegner ny graf
        #setter navn på akser og grafer
        plt.title("Høyde over tid - Siste 200 sekunder")
        plt.legend(loc="upper left")
        plt.xlabel("Tid (sekunder)")
        plt.ylabel("Høyde (meter)")
 
    except Exception as e:
        print(f"En feil oppsto ved oppdatering av grafen: {e}")
 
# Setter overskriften til grafen
plt.title("Høyde over tid")
 
# Oppretter en animasjon som oppdaterer grafen to ganger i sekundet
ani = FuncAnimation(plt.gcf(), update_graph, interval=500)

plt.show() # Viser grafen
