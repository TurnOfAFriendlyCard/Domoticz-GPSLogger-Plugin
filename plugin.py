"""
<plugin key="GPSLogger" name="GPS Logger Presence" author="marathon2010" version="2.2.2">
    <description>
        <h2>Domoticz GPS Logger Plugin - v2.2.2</h2>
        This plugin collects location data via GPS Logger app and stores in Domoticz via standard API.<br/>
    </description>
    <params>
        <param field="Mode1" label="Users GPSLogger" width="400px" required="true" default="user1;user2;user3;"/>
        <param field="Mode2" label="Fence size (m)"  width="75px"  required="true" default="50"/>
        <param field="Mode3" label="Map provider"    width="300px">
            <options>
                <option label="TomTom Maps"    value="TM"/>
                <option label="Open Streetmap" value="OSM" default="true" />
            </options>
        </param>
        <param field="Mode4" label="TomTom API Key" width="300px" required="false"/>
        <param field="Mode5" label="Debug"          width="75px">
            <options>
                <option label="True"  value="Debug"/>
                <option label="False" value="Normal"  default="true" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import datetime
import time

from math      import radians, cos, sin, asin, sqrt
from tomtomapi import tomtomapi
from osmapi    import osmapi

import json

class BasePlugin:

    def __init__(self):

        self.circleUser             = ''         # user being processed
        self.circleBattery          = 0          # battery percentage of mobile phone for user being processed
        self.circleLatitude         = 0          # latitude value of mobile phone for user being processed
        self.circleLongitude        = 0          # longitude value of mobile phone for user being processed
        self.circleLocationName     = ''         # location details of mobile phone for user being processed
        self.circleSpeed            = 0          # speed value of mobile phone for user being processed
        self.deviceUser             = []         # users in the circle (entered as parameter Mode1)
        self.fenceSize              = 0          # size of the fence to determine Home (entered as parameter Mode2)
        self.factorSpeed            = 3.6        # factor to convert speed from m/s to km/h
        self.myHomelat              = 0          # latutide home location (captured from Domoticz settings)
        self.myHomelon              = 0          # longitude home location (captured from Domoticz settings)
        self.locationNames          = []         # list of fixed locations stored in "locations.txt"
        self.membercount            = 0          # number of users in the circle (entered as parameter Mode1)
        self.numberDevicesPerMember = 6          # number of devices in Domoticz for each user
        self.numberItemsRawData     = 4          # number of fields reported by GPS Logger (4: latitude, longitude, speed and battery)
        self.selectedMap            = ''         # what map is used for addresses and distance ((entered as parameter Mode3)
        self.tomtomapikey           = ''         # what is the API key for TomTom if that map is used (entered as parameter Mode4)

        return

    def onStart(self):
        Domoticz.Log("onStart called")

        if (Parameters["Mode5"] == "Debug"):
            Domoticz.Debugging(1)

        if ("GPSLoggerPresence" not in Images):
            Domoticz.Debug('Icons Created...')
            Domoticz.Image('GPSLoggerIcons.zip').Create()
        iconPID = Images["GPSLoggerPresence"].ID

        # Get the location from the Settings
        if not "Location" in Settings:
            Domoticz.Log("Location not set in Preferences")
            return False
        
        # The location is stored in a string in the Settings
        loc            = Settings["Location"].split(";")
        self.myHomelat = float(loc[0])
        self.myHomelon = float(loc[1])
        Domoticz.Debug("Coordinates from Domoticz: " + str(self.myHomelat) + ";" + str(self.myHomelon))

        if self.myHomelat == None or self.myHomelon == None:
            Domoticz.Log("Unable to parse coordinates")
            return False

        self.fenceSize   = int(Parameters["Mode2"])
        self.deviceUser  = Parameters["Mode1"].split(";")
        self.membercount = int(Parameters["Mode1"].count(';'))+1
        Domoticz.Debug('Member Count '+str(self.membercount))

        if (len(Devices) == 0):
            for member in range (self.membercount):
                if (self.deviceUser[member] == ""):
                    Domoticz.Debug('User empty; index = '+str(member+1))
                else:
                    # create six devices and the last one (RawData) not being visible in the switches or utility tab.
                    Domoticz.Device(Name=self.deviceUser[member]+' Presence', Unit=(member*self.numberDevicesPerMember)+1, TypeName="Switch", Image=iconPID, Used=1).Create()
                    Domoticz.Device(Name=self.deviceUser[member]+' Location', Unit=(member*self.numberDevicesPerMember)+2, TypeName="Text", Used=1).Create()
                    Domoticz.Device(Name=self.deviceUser[member]+' Battery',Unit=(member*self.numberDevicesPerMember)+3, TypeName="Percentage", Used=1).Create()
                    Domoticz.Device(Name=self.deviceUser[member]+' Distance',Unit=(member*self.numberDevicesPerMember)+4, TypeName="Custom", Options={"Custom": "1;mins"}, Used=1).Create()
                    Domoticz.Device(Name=self.deviceUser[member]+' Speed',Unit=(member*self.numberDevicesPerMember)+5, TypeName="Custom", Options={"Custom": "1;km/h"}, Used=1).Create()
                    Domoticz.Device(Name=self.deviceUser[member]+' RawData',Unit=(member*self.numberDevicesPerMember)+6, TypeName="Text", Used=0).Create()
                    Domoticz.Debug('Devices: '+str(self.numberDevicesPerMember)+','+self.deviceUser[member])
            Domoticz.Debug(str(self.deviceUser))
            with open(Parameters["HomeFolder"]+"deviceorder.txt","w") as f:
                json.dump(self.deviceUser,f)
        else:
            with open(Parameters["HomeFolder"]+"deviceorder.txt") as f: self.deviceUser = json.load(f)
            Domoticz.Debug('Users are '+str(self.deviceUser))

        Domoticz.Debug("Devices available...")
        DumpConfigToLog()

        if (Parameters["Mode3"] == "OSM"):
            self.selectedMap = "OSM"
        else:
            self.selectedMap = "TM"
		
        if (Parameters["Mode4"] == ""):
            self.tomtomapikey = 'Empty'
        else:
            self.tomtomapikey = Parameters["Mode4"]

        try:
            with open(Parameters["HomeFolder"]+"locations.txt") as f:
                for line in f:
                    self.locationNames.append(line.rstrip('\n').split(','))
                Domoticz.Debug('Locations are '+str(self.locationNames))
        except:
            Domoticz.Log('No locations.txt file found')
			
        Domoticz.Heartbeat(15)

    def onStop(self):
        Domoticz.Log("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Connection, Data, Status, Extra):
        Domoticz.Log("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        Command = Command.strip()
        action, sep, params = Command.partition(' ')
        action = action.capitalize()
        params = params.capitalize()
 
        if Command=='Off':
            UpdateDevice(Unit,0,'Off')
        elif Command=='On':
            UpdateDevice(Unit,1,'On')

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Debug("onHeartBeat called.")
        for member in range (self.membercount):
             Domoticz.Debug('Processing '+str(member)+' RawData: '+Devices[member*self.numberDevicesPerMember+6].Name+' = "'+Devices[member*self.numberDevicesPerMember+6].sValue+'"')
             locData = Devices[member*self.numberDevicesPerMember+6].sValue.split(";")
             if self.numberItemsRawData == len(locData):
                 self.circleLatitude  = float(locData[0])
                 self.circleLongitude = float(locData[1])
                 self.circleSpeed     = round(float(locData[2])*float(self.factorSpeed))
                 self.circleBattery   = float(locData[3])

                 distanceToHome       = haversine(float(self.circleLatitude),float(self.circleLongitude),float(self.myHomelat),float(self.myHomelon))
                 presenceValue        = 0
                 presenceValueText    = ""
                 Domoticz.Debug('Fence (Actual/Defined) '+str(int(distanceToHome))+'/'+str(self.fenceSize))
                 if int(distanceToHome)<=int(self.fenceSize):                                                                              # Check within fence size
                     self.circleLocationName = "Home"
                     presenceValue           = 1
                     presenceValueText       = "On"
                 else:
                     self.circleLocationName = ""
                     presenceValue           = 0
                     presenceValueText       = "Off"

                     for line in self.locationNames[1:]:                                                                                   # Determine if in fence of a fixed location
                         distanceToLoc = haversine(float(self.circleLatitude),float(self.circleLongitude),float(line[1]),float(line[2]))
                         if int(distanceToLoc)<=int(line[3]):
                             self.circleLocationName=line[0]

                 UpdateDevice((member*self.numberDevicesPerMember)+1,presenceValue,presenceValueText)                                      # Presence Device
                 UpdateDevice((member*self.numberDevicesPerMember)+3,int(float(self.circleBattery)),str(int(float(self.circleBattery))))   # Battery Device
                 UpdateDevice((member*self.numberDevicesPerMember)+5,0,str(self.circleSpeed))                                              # Speed Device
#                 currentmin = 0
                 if self.circleLocationName != "":                                                                                         # Location either fixed location or Home
                     currentloc = self.circleLocationName
                 else:                                                                                                                     # Determine location via API on selected map
                     currentloc = None

                     if self.selectedMap   == "TM":
                         mapAPI = tomtomapi()
                     elif self.selectedMap == "OSM":
                         mapAPI = osmapi()

                     if self.selectedMap   == "TM":
                         currentstat2, currentloc = mapAPI.getaddress(self.tomtomapikey,self.circleLatitude,self.circleLongitude)
#                         currentstat, currentmin  = mapAPI.getdistance(self.tomtomapikey,self.circleLatitude,self.circleLongitude,self.myHomelat,self.myHomelon)
                     elif self.selectedMap == "OSM":
                         currentstat2, currentloc = mapAPI.getaddress(self.circleLatitude,self.circleLongitude)
#                         currentstat, currentmin  = mapAPI.getdistance(self.circleLatitude,self.circleLongitude,self.myHomelat,self.myHomelon)
                         time.sleep(1)                                                                                                     # In respect of OSM's usage policy of 1 call per second
                 UpdateDevice((member*self.numberDevicesPerMember)+2,1,currentloc)                                                         # Location Device
#                 UpdateDevice((member*self.numberDevicesPerMember)+4,0,currentmin)                                                         # Distance Device

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data, Status, Extra):
    global _plugin
    _plugin.onMessage(Connection, Data, Status, Extra)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

def haversine(lat1, lon1, lat2, lon2):

    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r * 1000
	
def UpdateDevice(Unit, nValue, sValue):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it 
    if (Unit in Devices):
        if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue):
            Devices[Unit].Update(nValue=nValue, sValue=str(sValue))
            Domoticz.Debug("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+")")
    return

    # Generic helper functions

def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
    return
