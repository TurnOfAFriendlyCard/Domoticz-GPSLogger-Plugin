"""
<plugin key="GPSLogger" name="GPS Logger Presence" author="marathon2010" version="3.0.1">
    <description>
        <h2>Domoticz GPS Logger Plugin - v3.0.1</h2>
        This plugin collects location data via GPS Logger app and stores in Domoticz devices via standard API.<br/>
    </description>
    <params>
        <param field="Mode1" label="Users GPSLogger"   width="400px"  required="true"   default="user1;user2;user3;"/>
        <param field="Mode2" label="Fence size (m)"    width="75px"   required="true"   default="50"/>
        <param field="Mode3" label="Map provider"      width="300px"  required="true" >
            <options>
                <option label="TomTom Maps"            value="TM"/>
                <option label="Open Streetmap"         value="OSM"                      default="true" />
            </options>
        </param>
        <param field="Mode4" label="TomTom API Key"    width="300px"  required="false"/>
        <param field="Mode5" label="Map presentation"  width="300px"  required="true" >
            <options>
                <option label="Google Maps"            value="GM"/>
                <option label="Open Streetmap"         value="OSM"                      default="true" />
            </options>
        </param>
        <param field="Mode6" label="Debug"             width="75px"   required="true" >
            <options>
                <option label="True"                   value="Debug"/>
                <option label="False"                  value="Normal"                   default="true" />
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import time

from math      import radians, cos, sin, asin, sqrt
from tomtomapi import tomtomapi
from osmapi    import osmapi
from datetime  import datetime

import json

class BasePlugin:

    def __init__(self):

        # variables used in the process
        self.circleUser             = ''         # user being processed
        self.circleBattery          = 0          # battery percentage of mobile phone for user being processed
        self.circleLatitude         = 0          # latitude value of mobile phone for user being processed
        self.circleLongitude        = 0          # longitude value of mobile phone for user being processed
        self.circleLatitudePrev     = 0          # latitude value of mobile phone for user being processed last time captured
        self.circleLongitudePrev    = 0          # longitude value of mobile phone for user being processed last time captured
        self.circleLocationName     = ''         # location details of mobile phone for user being processed
        self.circleSpeed            = 0          # speed value of mobile phone for user being processed
        self.deviceUser             = []         # users in the circle (entered as parameter Mode1)
        self.fenceSize              = 0          # size of the fence to determine Home (entered as parameter Mode2)
        self.mapBase                = ''         # Base part for map to be used to present location
        self.mapSeparator           = ''         # Separator of latitude and longitude for map to be used to present location 
        self.myHomelat              = 0          # latutide home location (captured from Domoticz settings)
        self.myHomelon              = 0          # longitude home location (captured from Domoticz settings)
        self.locationNames          = []         # list of fixed locations stored in "locations.txt"
        self.membercount            = 0          # number of users in the circle (entered as parameter Mode1)
        self.selectedMap            = ''         # what map is used for addresses and distance (entered as parameter Mode3)
        self.tomtomapikey           = ''         # what is the API key for TomTom if that map is used (entered as parameter Mode4)

        # constants used in the process
        self.codeGoogleMaps         = 'GM'        # short for usage Google Maps
        self.codeOpenStreetMaps     = 'OSM'       # short for usage Open StreetMaps
        self.codeTomTomMaps         = 'TM'        # short for usage Tom Tom Maps
        self.devPresence            = 1           # indicator Presence device in sequence of all devices defined
        self.devLocation            = 2           # indicator Location device in sequence of all devices defined
        self.devBattery             = 3           # indicator Battery device in sequence of all devices defined
        self.devDistance            = 4           # indicator Distance device in sequence of all devices defined
        self.devSpeed               = 5           # indicator Speed device in sequence of all devices defined
        self.devRawData             = 6           # indicator RawData device in sequence of all devices defined
        self.devMap                 = 7           # indicator Map device in sequence of all devices defined
        self.factorSpeed            = 3.6         # factor to convert speed from m/s to km/h
        self.numberDevicesPerMember = self.devMap # number of devices in Domoticz for each user
        self.numberItemsRawData     = 4           # number of fields reported by GPS Logger (4: latitude, longitude, speed and battery)
        self.timeDiff               = 60          # maximum number of seconds between actual time and last update location in order to update map device

        # define links for publishing location on maps, two types defined: Google Maps and Open Streetmap
        self.mapLink                = '<a href='
        self.mapGMBase              = '"http://www.google.com/maps/search/?api=1&query='                     # Google Maps base link
        self.mapGMSeparator         = ','                                                                    # Google Maps separator of latitude and longitude
        self.mapOSMBase             = '"https://www.openstreetmap.org/#map=16/'                              # Open StreetMaps base link
        self.mapOSMSeparator        = '/'                                                                    # Open StreetMaps separator of latitude and longitude
        self.mapSuffix              = '" target="_new">Click to Open Map</a>'

        return

    def onStart(self):
        Domoticz.Log("onStart called")

        # Debug mode required?
        if (Parameters["Mode6"] == "Debug"):
            Domoticz.Debugging(1)

        # Load the images
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

        # Capture input on fence size and users
        self.fenceSize   = int(Parameters["Mode2"])
        usrString        = Parameters["Mode1"]
        self.deviceUser  = usrString.split(";")
        self.membercount = int(usrString.count(';'))+1
        if usrString[-1] == ";":                                          # last character in userstring data entry is semi colon, so empty user
            self.membercount -= 1
 
        Domoticz.Debug('Member Count '+str(self.membercount) + ' for ' + str(usrString))

        if (len(Devices) == 0):
            for member in range (self.membercount):
                if (self.deviceUser[member] == ""):
                    Domoticz.Debug('User empty; index = '+str(member+1))
                else:
                    # create devices and RawData not being visible in the switches or utility tab.
                    Domoticz.Device(Name=self.deviceUser[member]+' Presence', Unit=(member*self.numberDevicesPerMember)+self.devPresence, TypeName="Switch"    , Image=iconPID               , Used=1).Create()
                    Domoticz.Device(Name=self.deviceUser[member]+' Location', Unit=(member*self.numberDevicesPerMember)+self.devLocation, TypeName="Text"                                    , Used=1).Create()
                    Domoticz.Device(Name=self.deviceUser[member]+' Battery',  Unit=(member*self.numberDevicesPerMember)+self.devBattery,  TypeName="Percentage"                              , Used=1).Create()
                    Domoticz.Device(Name=self.deviceUser[member]+' Distance', Unit=(member*self.numberDevicesPerMember)+self.devDistance, TypeName="Custom"    , Options={"Custom": "1;mins"}, Used=1).Create()
                    Domoticz.Device(Name=self.deviceUser[member]+' Speed',    Unit=(member*self.numberDevicesPerMember)+self.devSpeed,    TypeName="Custom"    , Options={"Custom": "1;km/h"}, Used=1).Create()
                    Domoticz.Device(Name=self.deviceUser[member]+' RawData',  Unit=(member*self.numberDevicesPerMember)+self.devRawData,  TypeName="Text"                                    , Used=0).Create()
                    Domoticz.Device(Name=self.deviceUser[member]+' Map',      Unit=(member*self.numberDevicesPerMember)+self.devMap,      TypeName="Text"                                    , Used=1).Create()
                    Domoticz.Debug('Devices: '+str(self.numberDevicesPerMember)+','+self.deviceUser[member])
            Domoticz.Debug(str(self.deviceUser))
            with open(Parameters["HomeFolder"]+"deviceorder.txt","w") as f:
                json.dump(self.deviceUser,f)
        else:
            with open(Parameters["HomeFolder"]+"deviceorder.txt") as f: self.deviceUser = json.load(f)
            Domoticz.Debug('Users are '+str(self.deviceUser))

        Domoticz.Debug("Devices available...")
        DumpConfigToLog()

        # Capture the Maps to present onto and request data from
        if (Parameters["Mode3"] == self.codeOpenStreetMaps):
            self.selectedMap    =  self.codeOpenStreetMaps
        if (Parameters["Mode3"] == self.codeTomTomMaps):
            self.selectedMap    =  self.codeTomTomMaps

        if (Parameters["Mode5"]  == self.codeOpenStreetMaps):
            self.mapSeparator    =  self.mapOSMSeparator 
            self.mapBase         =  self.mapLink + self.mapOSMBase
        if (Parameters["Mode5"]  == self.codeGoogleMaps):
            self.mapSeparator    =  self.mapGMSeparator 
            self.mapBase         =  self.mapLink + self.mapGMBase

        # Define the TomTom API key if any
        if (Parameters["Mode4"] == ""):
            self.tomtomapikey   = 'Empty'
        else:
            self.tomtomapikey   = Parameters["Mode4"]

        # Read the used defined locations
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
             Domoticz.Debug('Processing '+str(member)+' RawData: '+Devices[member*self.numberDevicesPerMember+self.devRawData].Name+' = "'+Devices[member*self.numberDevicesPerMember+self.devRawData].sValue+'"')
             locData = Devices[member*self.numberDevicesPerMember+self.devRawData].sValue.split(";")
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

                 UpdateDevice((member*self.numberDevicesPerMember)+self.devPresence,presenceValue,presenceValueText)                                   # Presence Device
                 UpdateDevice((member*self.numberDevicesPerMember)+self.devBattery,int(float(self.circleBattery)),str(int(float(self.circleBattery)))) # Battery Device
                 UpdateDevice((member*self.numberDevicesPerMember)+self.devSpeed,0,str(self.circleSpeed))                                              # Speed Device
#                 currentmin = 0
                 if self.circleLocationName != "":                                                                                         # Location either fixed location or Home
                     currentloc = self.circleLocationName
                 else:                                                                                                                     # Determine location via API on selected map
                     currentloc = None

                     if self.selectedMap   == self.codeTomTomMaps:
                         mapAPI            =  tomtomapi()
                     elif self.selectedMap == self.codeOpenStreetMaps:
                         mapAPI            =  osmapi()

                     if self.selectedMap   == self.codeTomTomMaps:
                         currentstat2, currentloc = mapAPI.getaddress(self.tomtomapikey,self.circleLatitude,self.circleLongitude)
#                         currentstat, currentmin  = mapAPI.getdistance(self.tomtomapikey,self.circleLatitude,self.circleLongitude,self.myHomelat,self.myHomelon)
                     elif self.selectedMap == self.codeOpenStreetMaps:
                         currentstat2, currentloc = mapAPI.getaddress(self.circleLatitude,self.circleLongitude)
#                         currentstat, currentmin  = mapAPI.getdistance(self.circleLatitude,self.circleLongitude,self.myHomelat,self.myHomelon)
                         time.sleep(1)                                                                                                     # In respect of OSM's usage policy of 1 call per second

                 UpdateDevice((member*self.numberDevicesPerMember)+self.devLocation,1,currentloc)                                          # Location Device

                 # Location device within Domoticz will be updated only if the actual location is changed (behavior of Domoticz). So for instance when a user remains at Home the map device
                 # does not need to be changed as well. Approach is to retrieve the last seen timestamp of the location device. If that is changed
                 # recently (within the last 60 seconds) also the map device will be updated.
                 # Class strptime within function datetime is not used as this sometimes results in "TypeError: 'NoneType' object is not callable".

                 timeCurrent    = str(datetime.now())
                 timeLastUpdate = str(Devices[member*self.numberDevicesPerMember+self.devLocation].LastUpdate)

                 # Example .now()     is 2022-03-01 14:30:15.123456
                 # Example LastUpdate is 2024-02-29 16:17:01
                 
                 if str(timeCurrent[0:10]) == str(timeLastUpdate[0:10]):                                                                   # Only checking time when same dates
                     Domoticz.Debug('Update Map ' + str(timeLastUpdate) + '; ' + str(timeCurrent))
                     timeDiff     = (int(timeCurrent[11:13]) - int(timeLastUpdate[11:13])) * 3600 + (int(timeCurrent[14:16]) - int(timeLastUpdate[14:16])) * 60 + int(timeCurrent[17:19]) - int(timeLastUpdate[17:19])
                     if timeDiff <= self.timeDiff:                                                                                         # Actual difference in seconds is with updated map checked difference
                         showMap  = self.mapBase + str(self.circleLatitude) + self.mapSeparator + str(self.circleLongitude) + self.mapSuffix        # Define link for click on maps text
                         UpdateDevice((member*self.numberDevicesPerMember)+self.devMap,1,showMap)                                          # Map Device

#                 UpdateDevice((member*self.numberDevicesPerMember)+self.devDistance,0,currentmin)                                          # Distance Device

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
