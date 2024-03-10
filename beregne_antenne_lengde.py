# Konstanter
lys_hastighet = 3 * 10**8  # lysets hastighet i meter per sekund
frekvens = 869.4 * 10**6  # Frekvensen i Hertz (869 MHz)

# Beregne bølgelengden
bølgelengde = lys_hastighet / frekvens

# Beregne lengden på en 1/4 monopole antenne
monopole_antenne_lengde = bølgelengde / 4
monopole_antenne_lengde_cm = monopole_antenne_lengde * 100
print(monopole_antenne_lengde_cm)# i cm
