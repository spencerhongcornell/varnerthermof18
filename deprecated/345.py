import numpy as np
import matplotlib.pyplot as plt
from sympy import solve, Eq, symbols
import sys 
import pandas
import math
# This function calculates the degradation of the COP based on each entropy generation term (S)
def degradeCOP(Tevap, Tcond, Qall, S):
	degraded = ((Tevap * Tcond)/(Tcond - Tevap)) * (S/Qall)
	return degraded

# This function calculates the reversible COP of a ES refrigerator based on thermal reservoirs
def reversibleCOP(Tevap, Tcond, Tgen):
	revCOP = (((Tgen - Tcond)/(Tgen))/((Tcond-Tevap)/Tevap))
	return revCOP

# This function solves the system of equations to calculate the mass flowrates of
# the combined absorber-evaporator system
def massabsorberevaporator(m6, m4, xa4, ya3, xa6):
	m3, m5= symbols(['m3', 'm5'])
	system = [
	#Eq((xa4*m4)+ (ya3 * m3) - (0 * m5) - (xa6 * m6), 0),
    Eq(m5 - (1-ya3)*m3,0),
	Eq(m4 + m3 - m5 - m6, 0),
    #Eq((1-ya3)*m3-m5, 0)
	#Eq(m4 - (ya3*m3) - (m5) + (ya3 * m6), 0)
	]
	soln = solve(system, [m4, m3, m5, m6])

	return float(m4), float(soln[m3]), float(soln[m5]), float(m6)

# This is an interpolate helper function to be used in other functions.
# targetcomp refers to ammonia composition. All CSV files are in ammonia composition.
def interpolate(filename, targetcomp):
	# done at 4 bar
	# must use the entropy-ammonia-water csv, entropy-ammonia-butane csv, or enthalpy-ammonia-water csv
	colnames = ['pressure', 'ammoniacomp', 'prop']
	data = pandas.read_csv('%s.csv' %filename, names=colnames)

	ammoniacomp = data.ammoniacomp.tolist()
	prop = data.prop.tolist()

	lower = prop[int(math.floor(targetcomp /0.05))]
	higher = prop[(int((math.floor(targetcomp /0.05))+1))]

	theta = (targetcomp - int(math.floor(targetcomp /0.05))*0.05 ) / ((int((math.floor(targetcomp /0.05))+1))*0.05 - int(math.floor(targetcomp /0.05))*0.05 )
	return (theta * higher) + (1-theta)*lower

# This calculates the two mass flowrates and the compositions coming out of the flash drum 
# given a mass flowrate and composition of ammonia coming in
# inputcomp is the ammonia composition
# temp is the temperature that the flash drum flashes at
def leverrule(inputflow, temp, inputcomp):
	#t-xy of ammonia-water
	#input composition of ammonia
	colnames = ['pressure', 'ammoniacomp', 'temperature', 'vaporwater', 'vaporammonia', 'liquidwater', 'liquidammonia']
	filename = 'txy-ammonia'
	data = pandas.read_csv('%s.csv' %filename, names = colnames)

	ammoniacomp = data.ammoniacomp.tolist()
	temperature = data.temperature.tolist()
	vaporammonia = data.vaporammonia.tolist()
	liquidammonia = data.liquidammonia.tolist()


	index, valuetemp =  min(enumerate(temperature), key=lambda x: abs(x[1]-temp))

	liquiddistance = inputcomp - liquidammonia[index]
	vapordistance = vaporammonia[index] - inputcomp

	vaporflow = symbols('vaporflow')
	system = [
	Eq((vapordistance * vaporflow) + (-1.0*liquiddistance*(float(inputflow) - vaporflow)), 0)
	]
	soln = solve(system, [vaporflow])

	# the order is: vapor flow, liquid flow, liquid ammonia composition. vapor ammonia composition
	return soln[vaporflow], (inputflow - soln[vaporflow]) ,liquidammonia[index], vaporammonia[index]

# This calculates the Q of the generator
# compin is the ammonia composition
def Qgenerator(massin, compin):
	massout = massin

	enthalpyin = interpolate('enthalpy-kjmol-325K-ammoniawater', compin)

	enthalpyout = interpolate('enthalpy-kjmol-345K-ammoniawater', compin)

	Qgen = -1*(massin*enthalpyin - massout*enthalpyout)

	return Qgen
# This calculates the S of the generator
# compin is the ammonia generator
def Sgenerator(massin, compin, Qgen):
	massout = massin

	entropyin = interpolate('entropy-kjmol-325K-ammoniawater', compin)
    #RAHUL fixed Line 95 - wrong entropy values read in
	entropyout = interpolate('entropy-kjmol-345K-ammoniawater', compin)

	Sgen = symbols('Sgen')
	system = [
	Eq((-1 * massin * entropyin ) + (massout*entropyout) + (Qgen/345) - Sgen, 0)

	]
	soln = solve(system, [Sgen])

	return soln[Sgen]
 
def Qevaporator(m2, m3, m5, ya3, ya2, xa5):

	enthalpym2 = interpolate('enthalpy-kjmol-345K-ammoniawater', ya2)
    #
	enthalpym3 = interpolate('enthalpy-kjmol-266K-ammoniabutane', ya3)
    #-94.38 kJ/mol
	enthalpym5 = interpolate('enthalpy-kjmol-325K-ammoniabutane', xa5)
    #-133kj/mol
	Qevap = symbols('Qevap')
	system = [
	Eq(( m2 * enthalpym2 ) + (-1* m3*enthalpym3) + (m5*enthalpym5) + Qevap, 0)

	]
	soln = solve(system, [Qevap])

	return soln[Qevap]

def Sevaporator(m2, m3, m5, ya3, ya2, xa5, T, Qevap):

	entropym2 = interpolate('entropy-kjmol-345K-ammoniawater', ya2)

	entropym3 = interpolate('entropy-kjmol-266K-ammoniabutane', ya3)

	entropym5 = interpolate('entropy-kjmol-325K-ammoniabutane', xa5)

	Sevap = symbols('Sevap')
	system = [
	Eq(( m2 * entropym2 ) + (-1* m3*entropym3) + (m5*entropym5) + (Qevap/T) - Sevap, 0)
	]

	soln = solve(system, [Sevap])

	return soln[Sevap]

def Qabsorber(m3, m4, m5, m6, ya3, xa4, xa5, xa6):

	enthalpym3 = interpolate('enthalpy-kjmol-266K-ammoniabutane', ya3)
    
	enthalpym4 = interpolate('enthalpy-kjmol-345K-ammoniawater', xa4)
    
	enthalpym5 = interpolate('enthalpy-kjmol-325K-ammoniabutane', xa5)
    
	enthalpym6 = interpolate('enthalpy-kjmol-325K-ammoniawater', xa6)
    
	Qabs = symbols('Qabs')
	system = [
	Eq((m3 * enthalpym3 ) + (m4 * enthalpym4) + (-1*m5 * enthalpym5) + (-1 * m6 * enthalpym6) + Qabs, 0)
	]

	soln = solve(system, [Qabs])

	return soln[Qabs]


def Sabsorber(m3, m4, m5, m6, ya3, xa4, xa5, xa6, Qabs, T):

	entropym3 = interpolate('entropy-kjmol-266K-ammoniabutane', ya3)

	entropym4 = interpolate('entropy-kjmol-345K-ammoniawater', xa4)

	entropym5 = interpolate('entropy-kjmol-325K-ammoniabutane', xa5)

	entropym6 = interpolate('entropy-kjmol-325K-ammoniawater', xa6)

	Sabs = symbols('Sabs')
	system = [
	Eq((m3*entropym3) + (m4 * entropym4) + (-1*m5 * entropym5) + (-1*m6*entropym6) + (Qabs/T)- Sabs, 0)
	]

	soln = solve(system, [Sabs])

	return soln[Sabs]

################
#    RAHUL     #
################ 
massoutgen = 10   # this is the mass flow rate of the stream coming out of the generator
compammoniagen = 0.2  # this is the composition of ammonia out of the generator
################
#    RAHUL     #
################



#massoutgen = float(sys.argv[1])
#massammoniaoutgen = massoutgen * float(sys.argv[2])
#masswateroutgen = massoutgen * (1-float(sys.argv[2]))
#compammoniagen = (massammoniaoutgen/massoutgen)
def run(ammoniacompin):

	massintoflash = massoutgen 
	massvaporoutflash, massliquidoutflash, liquidammoniacomp, vaporammoniacomp = leverrule(10, 345, ammoniacompin)


	m2 = massvaporoutflash
	ya2 = vaporammoniacomp

	m4 = massliquidoutflash

	m6old = massoutgen 
	xa4 =  liquidammoniacomp
	ya3 = 0.75    #AZEOTROPE
	xa6 = compammoniagen
	xa5 = 0        #ASSUME TO BE PURE STREAM - RAHUL


	m4, m3, m5, m6new = massabsorberevaporator(m6old, massliquidoutflash, xa4, ya3, xa6)
	#print("m2: " +  str(m2) + "\nm3: " + str(m3) +  "\n" + "m4: " + str(m4)+ "\n" + "m5: " + str(m5) + "\n" + "m6: " + str(m6new))
	Qevap = Qevaporator(m2, m3, m5, ya3, ya2, xa5)
	Sevap = Sevaporator(m2, m3, m5, ya3, ya2, xa5, 266, Qevap)

	#print("Qevap: " + str(Qevap) + "\nSevap: " + str(Sevap))


	Qabs = Qabsorber(m3, m4, m5, m6new, ya3, xa4, xa5, xa6)
	Sabs = Sabsorber(m3, m4, m5, m6new, ya3, xa4, xa5, xa6, Qabs, 325)

	#print("Qabs: " + str(Qabs) + "\nSabs: " + str(Sabs))

	Qgen = Qgenerator(m6new, xa6)
	Sgen = Sgenerator(m6new, xa6, 345)

	#print("Qgen: " + str(Qgen) + "\nSgen: " + str(Sgen))

	#print(Qevap/Qgen)
	#Sall = Sgen + Sevap + Sabs
	COPrev = reversibleCOP(266, 325, 345)

	return Qevap, m4, m3, Qgen

Qevapl = []
m4l = []
m3l = []
Qgenl = []
for i in np.arange(0, 1, 0.005):
	Qevap, m4, m3, Qgen = run(i)
	if Qevap > 0 and m4 > 0 and m3 > 0 and Qgen > 0:
		Qevapl.append(Qevap)
		m4l.append(m4)
		m3l.append(m3)
		Qgenl.append(Qgen)
		print(i)
#Sall = - Qevap/266 - Qabs/325 + Qgen/375

# Sall = [Sgen, Sevap, Sabs]
# COPdegrade = 0
# for S in Sall:
# 	COPdegrade += degradeCOP(266, 325, Qgen, S)

# print(COPdegrade)
#COPdegrade = degradeCOP(266, 325, 4000000, Sall)








