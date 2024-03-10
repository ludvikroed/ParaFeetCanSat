strekning = 1000

masse = 300
gravitasjonskonstant = 9.81 # m/s**2
luftmotstandskoeffisient = 1.71
lufttrykk = 0.001225 # g/cm**3
diameter = 33
radius = diameter/2
areal = 3.141592653589793 * (radius*radius)

v=((2 * (masse/1000) * gravitasjonskonstant)/(luftmotstandskoeffisient * (lufttrykk*1000) * (areal/100**2)))**0.5
avrundet_v=round(v, 2)

tid = strekning / avrundet_v
avrundet_tid = round(tid, 2)

print("")
print("Den terminale hastigheten til cansat-en er", avrundet_v, "m/s.")
print("Med en fart på", avrundet_v, "m/s, vil cansat-en bruke", avrundet_tid, "sekunder på en strekning på", strekning, "meter.")
print("")
