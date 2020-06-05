#!/usr/bin/python
from configparser import ConfigParser
from gpiozero import Button 
from gpiozero import OutputDevice 
import time
import urllib2
import os
import datetime
import signal
import sys, getopt
import keyboard

#define global vars
marquee = OutputDevice(2, active_high=False, initial_value=True) # Marquee is connected to GPIO2. Change the number in this line in case connected to other pin. 
TV = OutputDevice(4,  active_high=False, initial_value=True)  #
button = Button(3)  # Power button connected to GPIO3. Change the number in this line if it is on another pin. it is however highly recommnended not to use another pin, but to connect this button to pin 5 (gpio3) and ping 6 (GND), cause this will make the power button als bootup the pi from  a halted state
pf = "/tmp/button.pid" #name of pid file
logfilename = "" #location of logfile
timestamp = datetime.datetime.now()
state = 0 # 0=both on, 1 = Only TV on, 2=only Marquee on, 3 = both off.
debug = False
ignorepidfile=False
PowerSave=False
counter=0
ScreenSaver=False
screensavetimeout=0
ScreenSaving=False
Simple=False
screensaveroverrides=""

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

def On_Button_Press():
    global timestamp

    Debug("Event: Power Button Pressed")
    timestamp = datetime.datetime.now()
    
    #disable screensaver if it was active
    #DeactivateScreensaver()

        
def HandleState():        
    # handling state
    if state==0:
        Log("switching on tv and marquee")
        TV.on()
        marquee.on()
        RestorePower()
    elif state==1:
        Log("switching on tv, switching off marquee")
        TV.on()
        marquee.off()
        RestorePower()
    elif state==2:
        Log("switching off tv, switching on marquee")
        TV.off()
        marquee.on()
        SavePower()
    elif state==3:
        Log("switching off tv and marquee")
        TV.off()
        marquee.off()
        SavePower()
    else:
        Log("Error: Unknown state")

def CheckForRunningProcesses(processes):
    #global var to check if any process was found
    processfound=False

    #process procesnames
    splittedprocessnames=processes.split(",")
    for processname in splittedprocessnames:
        Debug ("Checking for "+processname)
        tmp = os.popen("ps -Af").read()
        proccount = tmp.count(processname)
        if proccount > 0:
            Debug(str(proccount)+' processes running of '+processname+'type')
            processfound=True
        else:
            Debug(processname+' not active')

    if processfound:
        Debug('One or more processes found, do not activate screensaver')
    else:
        Debug('Screensaver can be actived')

    return processfound


def ActivateScreensaver():
    global ScreenSaving
    global state
    
    if (CheckForRunningProcesses(screensaveroverrides)):
        Debug("Not activating because an override process is active...")
    else:
        Log("Activating screensaver")
        ScreenSaving=True
        state=3
        HandleState()

def DeactivateScreensaver():
    global ScreenSaving
    global state
    
    if (ScreenSaving):
        Log("Deactivating Screensaver")
        ScreenSaving=False
        state=0
        HandleState()
    else:
        Debug("Not deactivating screensaver")

def NextState():
    global state

    #Inc state (unless it's 3, then it should return to state 0
    if state<3:
        state+=1
    else:
        state=0

    #Toggle the pins
    HandleState()

def On_Button_Release():
    global timestamp
    global state

    Debug("Event: Power button released")

    #check if press was long enough
    timestamp2=datetime.datetime.now()
    delta=timestamp2-timestamp
    milliseconds=int(delta.total_seconds()*1000)
    Debug("button release after "+str(milliseconds)+" milliseconds")
    if milliseconds<10:
        Debug("too short, Ignoring event")
    else:
        #we have a valid press
        if (ScreenSaving):
            DeactivateScreensaver()
        else:
            if Simple:
                if state==0:
                    state=3
                    Debug("Simple mode: switching off tv and marquee")
                else:
                    Debug("Simple Mode: Switching on tv and marquee")
                    state=0
                #Make sure the state is handled
                HandleState()
            else:
                NextState()

    #Update timestamp for sreensaver
    timestamp=timestamp2

def On_Keyboard_Event(event):
    global timestamp
    global state

    Debug("Keyboard Event: " +str(event.name)+", "+str(event.event_type))
    #resetting timestamp to prevent screensaver kicking in
    timestamp=datetime.datetime.now()

    if (ScreenSaving):
        #disable screensaver if it was active
        DeactivateScreensaver()
    else:
        #if state=2 (TV off) or 3 (everything off), switch to state 0 at keyboard event
        if (state==2 or state==3):
            Debug("State was 2 or 3 on keyboard event, switching to 0")
            state=0
            HandleState()
        else:
            Debug("Ignoring keyboard event")

def Worker():
    global counter
    global ScreenSaving
    #Do some logging
    Log("mainworker started....")
    
    Debug("Worker: Screensavetimeout = "+str(screensavetimeout))

    #Main loop
    try:
        while True:
            time.sleep(1)

            if button.is_pressed:
                #increade seconds counts
                counter+=1

                #check if we have to reboot or shutdown
                if counter>3:
                    if Simple:
                        Log("Button pressed for 3 seconds, Restarting....")
                        marquee.on()
                        TV.on()
                        os.system("sudo init 6")
                    else:
                        Log("Button pressed for 3 seconds, Shutting down....")
                        marquee.on()
                        TV.on()
                        os.system("sudo init 0")
            else:
                #button not pressed, resetting timer
                counter=0

            #Check if we have to start screensaving
            if (ScreenSaver and not ScreenSaving):
                #calculate time difference
                timestamp2=datetime.datetime.now()
                delta=timestamp2-timestamp
                elapsedseconds=int(delta.total_seconds())
                #Debug("Time to screensaver = "+str(screensavetimeout-elapsedseconds))
                if (elapsedseconds>=screensavetimeout):
                    ActivateScreensaver()

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

    #Set functions on power button inputs
    button.when_pressed = On_Button_Press 
    button.when_released = On_Button_Release

    #SetKeyboadrd hook for screensaving function
    keyboard.hook(On_Keyboard_Event)

def Usage():
      print 'button.py [-h] [-f] [-i] [-c] [-p pidfile] [-l logfile] [-s timeout in seconds]'

def ReadConfig(ConfigFile):
    global pf
    global logfilename
    global debug
    global ignorepidfile
    global PowerSave
    global ScreenSaver
    global screensavetimeout
    global Simple
    global screensaveroverrides

    Log("Reading config from file "+ConfigFile)

    config=ConfigParser()
    config.read(ConfigFile)

    try:
        debug=config.getboolean('button','debug')
        Debug("Debugging on...")
        pf=config.get('button','pidfile')
        Debug("PF = "+pf)
        logfilename=config.get('button','logfile')
        Debug("logfile = "+logfilename)
        ignorepidfile=config.getboolean('button','force')
        Debug("Ignorepidfile = "+str(ignorepidfile))
        PowerSave=config.getboolean('button','powersave')
        Debug("powersave = "+str(PowerSave))
        screensavetimeout=config.getint('button','screensavetimeout')
        Debug("Screensavetimeout = "+str(screensavetimeout))
        ScreenSaver=config.getboolean('button','ScreenSaver')
        Debug("ScreenSaver = "+str(ScreenSaver))
        screensaveroverrides=config.get('button','screensaveroverrides')
        Debug("ScreenSaverOverrides = "+screensaveroverrides)
        Simple=config.getboolean('button','simplemode')
        Debug("SimpleMode = "+str(Simple))
    except Exception:
        Log("Error reading configfile")
        sys.exit(2)

def main(argv):
    # Check command line options
    global pf
    global logfilename
    global debug
    global ignorepidfile
    global PowerSave
    global ScreenSaver
    global screensavetimeout
    global Simple

    try:
        opts, args = getopt.getopt(argv,"hihdfdp:l:s:c:",["pidfile=","logfile=","help","force","debug","screensavetimeout=","cpupowersaving","simple","configfile="])
    except getopt.GetoptError:
        Usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            Debug("-h was specified")
            Usage()
            sys.exit(0)
        elif opt in ("-d", "--debug"):
            debug=True
            Debug("Debugging is enabled")
        elif opt in ("-i", "--simple"):
            Simple=True
            Debug("Simple Mode is enabled")
        elif opt in ("-c", "--configfile"):
            configfile = arg
            Debug("Using configfile "+configfile)
            ReadConfig(configfile)
        elif opt in ("-p", "--pidfile"):
            pf = arg
            Debug("Pidfile changed to "+pf)
        elif opt in ("-d", "--cpupowersaving"):
            PowerSave=True;
            Log("CPU Powersaving on...")
        elif opt in ("-s", "--screensavetimeout"):
            ScreenSaver=True
            screensavetimeout=int(arg) 
            Debug("Activate screensaver after "+str(screensavetimeout)+" seconds")
        elif opt in ("-l", "--logfile"):
            logfilename = arg
            Debug("Logfile changed to "+logfilename)
        elif opt in ("-f", "--force"):
            Log("ignoring existing pidfile("+pf+")")
            ignorepidfile=True;

    #Initialize and start worker 
    Initialize()
    Worker()


## Startup Main
if __name__ == "__main__":
   main(sys.argv[1:])
