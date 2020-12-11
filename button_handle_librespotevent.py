#!/usr/bin/python
from configparser import ConfigParser
import urllib2
import os
import sys, getopt
import datetime

#define global vars
logfilename = "" #location of logfile
spotifyplaysfile = "" #location of file which exists if spotify is playing
debug = False
configfile = "/etc/button.ini" #default location

def Log(tekst):
    if len(logfilename)==0:
        print tekst
    else:
        f = open(logfilename, "a+")
        f.write(str(datetime.datetime.now())+" HandleSpotifyEvent:"+str(tekst)+"\n")
        f.close

def Debug(tekst):
    if debug:
        if len(logfilename)==0:
            print "Debug: "+str(tekst)
        else:
            if debug:
                f = open(logfilename, "a+")
                f.write(str(datetime.datetime.now())+" HandleSpotifyEvent:Debug: "+str(tekst)+"\n")
                f.close

def ListEnvVars():
    if debug:
        Debug("List of Env Vars:")
        for i, j in os.environ.items():
            Debug(" "+str(i)+"="+str(j))

def Usage():
    print 'button_handle_librespotevent -c <configfilefile>'

def ReadConfig(ConfigFile):
    global logfilename
    global spotifyplaysfile
    global debug
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
        spotifyplaysfile=config.get('button','spotifyplaysfile')
        Debug("Spotifyplaysfile = "+spotifyplaysfile)
    except Exception:
        Log("Error reading configfile")
        sys.exit(2)

def main(argv):
    global configfile

    #Get config
    try:
        opts, args = getopt.getopt(argv,"c:",["configfile="])
    except getopt.GetoptError:
        Usage()
        sys.exit(2)

    if spotifyplaysfile==None:
        Usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-c", "--configfile"):
            configfile = arg


    #Load configfile
    Debug("Using configfile "+configfile)
    ReadConfig(configfile)

    #
    Event=os.getenv('PLAYER_EVENT')
    TrackID=os.getenv('TRACK_ID')
    #Log("Event = "+str(Event)+", TrackID="+str(TrackID))
    ListEnvVars()

    if Event=="start" or Event=="change" or Event=="playing":
        Log("Creating triggerfile")
        f = open(spotifyplaysfile, "a+")
        f.write(str(datetime.datetime.now())+" HandleSpotifyEvent: "+Event+" with song "+ TrackID +"\n")
        f.close

    if Event=="stop" or Event=="paused":
        Log("Deleting triggerfile")
        try:
            os.remove(spotifyplaysfile)
        except:
            Log("Error deleting spotifyplaysfile")



## Startup Main
if __name__ == "__main__":
   main(sys.argv[1:])
