from pylab import *
#from matplotlib.pyplot import *

#the following is data for the coeffecient of drag for a bullet at different speeds
# according to wikipedia (http://en.wikipedia.org/wiki/External_ballistics)
# this is for very low drag bullets
# I have data for the mach number and the drage
machl =array([0,0.2,0.45,0.55,0.65,0.75,0.8125,0.8375,0.8625,0.8875,0.9125,0.9375,0.9625,
0.9875,1.0125,1.0375,1.0625,1.0875,1.125,1.175,1.25,1.35,1.45,1.55,1.7,1.9,2.1,2.3])
Cl = [0.23,0.229,0.2,0.171,0.164,0.144,0.141,0.137,0.137,0.142,0.154,0.177,0.236,0.306,
0.334,0.341,0.345,0.347,0.348,0.348,0.343,0.336,0.328,0.321,0.304,0.292,0.282,0.27]
mach = 340#m/s at sea level at 15 C
n=28 #items in the above data set




#this is for the 30-06

m=0.0097 #kg
g = 9.81 #N/kg
#the terminal velocity is one way to calculate the air resistance
y = 0 #m - initial y positoin

#This is stuff to calculate the density of the air as it changes with height
p0 = 101325 #pa (sea level pressure)
T0 = 288.15 #K at sea level
g = 9.81
L = 0.0065 #K/m - temp lapse rate, whatever that means
R = 8.31447 #J/(mol K)
M = 0.0289644 #molar mass of air
T = T0 - L*y
p = p0*(1-L*y/T0)**(g*M/(R*L))
rho = p*M/(R*T)

#I want to use Fair = .5 rho CA *v^2, 
# I know at 100 mph, it is terminal velocity (0.13 mach) - this gives a drag coeff of 0.23
# So, Fair = mg =.5 rho A (0.23)(44.7)^2 - I can solve for A


scale = 1
clplot=[]
terminal_v = 44.7 #m/s  need to convert - I know this 100 mph
A = 2*m*g/(rho*Cl[0]*terminal_v**2)
vi = 880# m/s initial velocity



A=pi*(7.823e-3/2)**2
print A
t = 0.0 #seconds
dt = 0.01 #seconds
a = -g #initial acceleration
F = -m*g  #this is the net force
y_p = [y]   #for plotting y
v_p = [vi] #for plotting v
a_p = [a] # for plotting a
t_p = [t]
yff=y
yffp=[yff]
vff=vi
vffp=[vff]
updown = -1 #-1 if up, 1 if down
v=vi
initialv=[vi]  #an array for plotting v-init vs. flight time
dv = 5 # m/s  - this is my initial velocity increment
ymax = y #this is a keeper for finding out how high the guy goes
ymaxp=[ymax] #ymax array for plotting

#need stuff for no air resistance
yff = y #this is for free fall without air resistance
vff = vi




while y>=0:
    if v>0:
        updown=-1
    else:
        updown=1
    #need to determine speed to determine drag coeff
    for f in range(n):
        if v/mach>machl[f]:
            C = Cl[f]
    clplot=clplot+[scale*C]
    F = -m*g +updown*.5*A*rho*C*v**2 #the updown coef makes this the correct direction in this 1-d case
    a = F/m
    v=v+a*dt
    y=y+v*dt
    #vff=vff-g*dt
    #yff=yff+vff*dt
    t=t+dt

    #recalc density
    T = T0 - L*y
    p = p0*(1-L*y/T0)**(g*M/(R*L))
    rho = p*M/(R*T)
    #if y>ymax:
     #   ymax=y
   # print 'time = ', t, '  velocity = ', vi
    #t_p=t_p+[t]
    #initialv=initialv+[vi]
    #vi=vi+dv
    #ymaxp = ymaxp+[ymax]
    y_p=y_p+[y]
    v_p = v_p +[v]
    a_p = a_p +[a]
    t_p = t_p+[t]
   # yffp=yffp+[yff]
   # vffp=vffp+[vff]

#now it is time to make the plot
clplot=clplot+[scale*C]
plot(t_p, y_p,  linewidth=3)
#plot(v_p, clplot, linewidth=3)
#plot(t_p, affp, linewidth=3, label='free fall')
title('Height of .30-06 bullet')
#legend()
xlabel('time [s]')
ylabel('height [m]')
grid(color='b', linestyle='-', linewidth=0.5)
#annotate('local max', xy=(2, 1), xytext=(3, 1.5))
print t
print v
show()



