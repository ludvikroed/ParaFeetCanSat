
masse = 300 #massen til vår CanSat er 300 gram
gravitasjonskonstant = 9.81 # gravitasjonen til jorda
luftmotstandskoeffisient = 1.75 # Ca. luftmotstanden til en fallskjerm
lufttrykk = 0.001225 # g/cm**3
diameter = 33 # diameteren til fallskjermen i cm. 20,5cm og 33cm

radius = diameter/2
areal = 3.141592653589793 * (radius*radius)
masse_i_kg = masse/1000

terminal_hastighet = ((2 * masse_i_kg * gravitasjonskonstant)/(luftmotstandskoeffisient * (lufttrykk*1000) * (areal/100**2)))**0.5 # vi bruker formelen for terminal hastighet og regner ut terminal hastighet
avrundet_terminal_hastighet = round(terminal_hastighet, 2) # Vi runder av til to desimaler for å få et lesbart tall

print("Den terminale hastigheten til cansat-en er", avrundet_terminal_hastighet, "m/s med en fallskjerm med en diameter på:", diameter, "cm")
