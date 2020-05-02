#!/usr/bin/python
from gpiozero import Button 
from gpiozero import OutputDevice 
import time
import urllib2
import os
import datetime
import signal


#define global vars
marquee = OutputDevice(2, active_high=False) # Marque is on 
button = Button(3)  # pin 5 
TV = OutputDevice(4,  active_high=False)  #
pf = "/tmp/button.pid" #name of pid file
logfilename = "/var/log/button/button.py.log" #location of logfile
timestamp = datetime.datetime.now()
state = 0 # 0=both on, 1 = Only TV on, 2=only Marquee on, 3 = both off.

def Log(tekst):
    f = open(logfilename, "a+")
    f.write(str(datetime.datetime.now())+" "+str(tekst)+"\n")
    f.close

def GracefulKill(signum,frame):
    Log("Gracefull exit, removing PID file and cleaning up GPIO")
    os.remove(pf)
    quit()


def Button_Press():
    global timestamp

    Log("Event: Button Pressed")
    timestamp = datetime.datetime.now()

def Button_Release():
    global timestamp
    global state

    timestamp2=datetime.datetime.now()
    delta=timestamp2-timestamp
    milliseconds=int(delta.total_seconds()*1000)
    Log("button release after "+str(milliseconds)+" milliseconds")
    if milliseconds<50:
        Log("too short, Ignoring event")
    else: 
        #Log("Shutdown button pressed, shutting down")
        #os.system("sudo init 0")

        # change to next state
        if state<3:
            state+=1
        else:
            state=0

        # handling state
        if state==0:
            Log("State = 0: switching on tv and marquee")
            TV.off()
            marquee.off()
            Log ("Setting cpu governer back to normal (ondemand)")
            os.system("sudo cpufreq-set -g ondemand")

        elif state==1:
            Log("State=1: switching on tv, switching off marquee")
            TV.off()
            marquee.on()
        elif state==2:
            Log("State=2: switching off tv, switching on marquee")
            TV.on()
            marquee.off()
        elif state==3:
            Log("State=3: switching off tv and marquee")
            TV.on()
            marquee.on()
            Log ("Setting cpu governer to powersave")
            os.system("sudo cpufreq-set -g powersave")


#Prevent runing twice: check if PID is there, if not: Create PID file
if os.path.exists(pf):
    Log("PID file aready there: not starting")
    quit()
else:
    f=open(pf,'w')
    f.write(str(os.getpid()))
    f.close()

#make sure we remove the pid file when a kill signal is received
signal.signal(signal.SIGINT, GracefulKill)
signal.signal(signal.SIGTERM, GracefulKill)

#Set functions on button inputs
button.when_pressed = Button_Press 
button.when_released = Button_Release

#Do some logging
Log("Starting main loop....")

#Main loop
try:
  counter=0
  while True:
      time.sleep(1)
      if button.is_pressed:
          counter+=1
          Log("Counter="+str(counter))
          if counter>3:
            Log("Button pressed for 3 seconds, Shutting down....")
            marquee.off()
            TV.off()
            os.system("sudo init 0")
      else:
        counter=0
except KeyboardInterrupt:
  Log("Keyboard interrupt, removing PID file")
  os.remove(pf)

