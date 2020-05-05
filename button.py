#!/usr/bin/python
from gpiozero import Button 
from gpiozero import OutputDevice 
import time
import urllib2
import os
import datetime
import signal
import sys, getopt

#define global vars
marquee = OutputDevice(2, active_high=False, initial_value=True) # Marquee is connected to GPIO2. Change the number in this line in case connected to other pin. 
TV = OutputDevice(4,  active_high=False, initial_value=True)  #
button = Button(3)  # Power button connected to GPIO3. Change the number in this line if it is on another pin. it is however highly recommnended not to use another pin, but to connect this button to pin 5 (gpio3) and ping 6 (GND), cause this will make the power button als bootup the pi from  a halted state
pf = "/tmp/button.pid" #name of pid file
logfilename = "" #location of logfile
timestamp = datetime.datetime.now()
state = 0 # 0=both on, 1 = Only TV on, 2=only Marquee on, 3 = both off.
debug = False;
ignorepidfile=False;
PowerSave=False;
counter=0;

def Log(tekst):
    if len(logfilename)==0:
        print tekst
    else:
        f = open(logfilename, "a+")
        f.write(str(datetime.datetime.now())+" "+str(tekst)+"\n")
        f.close

def Debug(tekst):
    if debug:
        if len(logfilename)==0:
            print "Debug: "+str(tekst)
        else:
            if debug:
                f = open(logfilename, "a+")
                f.write(str(datetime.datetime.now())+" Debug: "+str(tekst)+"\n")
                f.close

def GracefulKill(signum,frame):
    Log("Gracefull exit, removing PID file and cleaning up GPIO")
    os.remove(pf)
    quit()

def SavePower():
    if PowerSave:
        Log ("Setting cpu governer to powersave")
        os.system("sudo cpufreq-set -g powersave")

def RestorePower():
    if PowerSave:
        Log("Setting cpu governer back to normal (ondemand)")
        os.system("sudo cpufreq-set -g ondemand")

def Button_Press():
    global timestamp

    Debug("Event: Button Pressed")
    timestamp = datetime.datetime.now()

def Button_Release():
    global timestamp
    global state

    timestamp2=datetime.datetime.now()
    delta=timestamp2-timestamp
    milliseconds=int(delta.total_seconds()*1000)
    Debug("button release after "+str(milliseconds)+" milliseconds")
    if milliseconds<50:
        Debug("too short, Ignoring event")
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
            Log("Button Pressed, switching on tv and marquee")
            TV.on()
            marquee.on()
            RestorePower()
        elif state==1:
            Log("Button Pressed, switching on tv, switching off marquee")
            TV.on()
            marquee.off()
            RestorePower()
        elif state==2:
            Log("Button pressed, switching off tv, switching on marquee")
            TV.off()
            marquee.on()
            SavePower()
        elif state==3:
            Log("Button Pressed, switching off tv and marquee")
            TV.off()
            marquee.off()
            SavePower()

def Worker():
    global counter
    #Do some logging
    Log("Button.py started....")

    #Main loop
    try:
        while True:
            time.sleep(1)
            if button.is_pressed:
                Debug("Counter="+str(counter))
                counter+=1
                Debug("Counter="+str(counter))
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


def Initialize():
    Debug ("Logfile="+logfilename+", pidfile="+pf)
    #Prevent runing twice: check if PID is there, if not: Create PID file
    if os.path.exists(pf):
        if ignorepidfile:
            Debug("Pidfile already there, but -f specified, so ignoring...")
        else:
            Log("PID file already there: not starting, use -f option if you want to force start")
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

def Usage():
      print 'button.py [-h] [-f] [-d] [-p pidfile] [-l logfile]'

def main(argv):
    # Check command line options
    global pf
    global logfilename
    global debug
    global ignorepidfile
    global PowerSave

    try:
        opts, args = getopt.getopt(argv,"hdfsp:l:",["pidfile=","logfile=","help","force","debug"])
    except getopt.GetoptError:
        Usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            Usage()
        elif opt in ("-d", "--debug"):
            debug=True
            Debug("Debugging is enabled")
        elif opt in ("-p", "--pidfile"):
            pf = arg
            Debug("Pidfile changed to "+pf)
        elif opt in ("-s", "--powersave"):
            PowerSave=True;
            Debug("Powersaving on...")
        elif opt in ("-l", "--logfile"):
            logfilename = arg
            Debug("Logfile changed to "+logfilename)
        elif opt in ("-f", "--force"):
            Debug("-f specified, ignoring existing pidfile("+pf+")")
            ignorepidfile=True;

    
    #Initialize and start worker 
    Initialize()
    Worker()


## Startup Main
if __name__ == "__main__":
   main(sys.argv[1:])
