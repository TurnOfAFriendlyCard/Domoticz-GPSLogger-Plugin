# Plugin:  Domoticz GPS Logger 
# Author:  marathon2010
# Date:    February 2024
# Version: 20

GOAL
Capture location data obtained via GPS Logger app into Domoticz devices.

DESCRIPTION
A mobile phone is used to capture actual location data. The app used for this plugin is GPS Logger,
however other GPS logging apps can be used as well. In fact the most important requirement is that the
app is able to share location data via the Domoticz API on regular basis.

Concept is that users are determined for these mobile phones (just names, no formal users in Domoticz).
Besides that the home location is identified by the location setup in Domoticz. A fence around the home
location determines how Home is identified. For example a circle of 100 meters around the address
Coolsingel 40, Rotterdam, the Netherlands (latitude 51.922710 and longitude 4.479160).

Multiple mobile phones are able to setup the connection with Domoticz, so in fact a family circle
can be setup for logging data and processing that data into Domoticz. For instance triggers in Domoticz
can be build to switch of the lights when all mobile phone users left the house. Or switch on when one of the
mobile phone users arrive at home. Or the alarm system can be triggered (switch on when all mobile phone users
left the house and switch off when one mobile phone users arrives at home).

Next devices will be created and updated in Domoticz (in the utility tab unless otherwise specified):
1. Presence: This is an On/Off switch indicating the user is within the fence (in switches tab).
2. Location: Text describing what the actual location of the user is.
3. Battery:  Charging percentage of the battery of the user.
4. Distance: Distance in minutes of the actual location to the fence (to implement in future).
5. Speed:    Speed in kilometers / hour of the user.
6. RawData:  Data which is captured from the GPS Logger app. This device is hidden (only in devices tab).

INSTALLATION / SETUP
A. PLUGIN
1. Open a putty session.
2. In the session go to the Plugin folder of Domoticz.
3. Create a folder for the plugin (mkdir Domoticz-GPSLogger).
4. Go to that folder (cd Domoticz-GPSLogger).
5. Download the Plugin: git clone https://github.com/TurnOfAFriendlyCard/Domoticz-GPSLogger-Plugin
6. Make de plugin.py file executable (chmod 755 plugin.py).
7. Restart Domoticz.

B. Domoticz
1. In the hardware tab a new type will be available: GPS Logger Presence.
2. Create the new hardware:
2a. Enter a logical name (for instance Location). Will be a suffix to all devices created.
2b. Enter the names of user of the mobile phones. Just logical name, not a Domoticz username. Separate with semicolons.
2c. Enter the fence size in meters of the Home location. Within this fence Home is determined.
2d. Select the map providor (either Open Streetmap or TomTom).
2e. For TomTom obtain an API key (see History on how-to).
2f. When required debug message can be shown in the Domoticz log (see Debug on True).
2g. Press Add to complete the installation.
4. Devices as summarized above will be created and plugin will be started.
5. Determine the Idx number in the devices tab for the "RawData" devices. These are required for GPS Logger.
6. Create a specific user for the GPS Logger integration. Rights "User" and Active Menu none. No devices need to be set.

C. ENCODE USER/PASSWORD
1. Go to the website https://www.base64encode.org/ to encode username and password into Base64 format.
2. Click on Encode.
3. Enter <username>:<password> into the text box. This the user in step B6. Also include the colon.
4. Output is something like bG9jYXRpb246cGFzc29mbG9jNDk4

D. GPS LOGGER
The Android app GPS is described at https://gpslogger.app/. Installation of the app is via F-Droid. Step to take are:
1. Open a webbrowser on the mobile phone.
2. Go to https://f-droid.org/
3a. Click on Download F-Droid.
3b. Once download is completed, open the F-Droid.apk.
3c. Install F-Droid app.
4. Open F-Droid app.
4a. Application sources will be updated.
4b. Click on the green search glass in the right-corner.
5. In the search bar on the top side of the screen enter "GPSLogger".
6. Click on Install button to instal the GPSLogger app.
7. Open GPSLogger app (vs 129 was used during plugin v2.2 development).
7a. Approve authorizations (location, files/photo's and battery background).
8. In Logging details switch on "Log to custom URL" and switch off "Log to GPX".
9. In Performance set "Logging Interval" to for instance 15 seconds (so data is shared to Domoticz with this interval).
10. In Custom URL switch on "Log to custom URL" (should be switched on already).
11. Click on URL and enter servername, port and body. Should look like this
https://example.com:443/json.htm?type=command&param=udevice&idx=<Idx>&nvalue=0&svalue=%LAT;%LON;%SPD;%BATT
For <Idx> enter the value determined in step B5.
12. Click on HTTP Headers and enter 
Content-Type: application/json
Authorization: Basic <base64>
The value of <base64> is the value generated in step C4.
13. Click on HTTP Method and set value to POST.
14. If a secure connection is used, click on validate SSL certificate (will show pop-up).
15. On the main screen click on Start Logging.
16. Data is now flowing from the GPSLogger app to the RawData device.
17. The GPSLogger can be closed, will run in the background.
18. Repeat these steps for every mobile phone involved. Take care to use different Idx numbers (step D11).

HISTORY 
The concept is based on the Life360 Plugin by fibalci.
He thanked Harper Reed for Python implementation of Life 360 API: https://github.com/harperreed/life360-python
The icons are downloaded from "Free Vector Graphics by www.Vecteezy.com"
"TomTom API key is not required, but if you want to get current address of a member and driving distance,
you should get a TomTom API key and copy-paste here, otherwise leave it empty.
How to get a TomTom API Key:
Go to https://developer.tomtom.com/user/register page.
Create a new User Account.
Login to your account and from 'My Apps',
press 'Add a new app' to add a new app and select at least 'Routing API' and 'Search API',
you can select all APIs here if you want.
Then from the 'Keys' page, copy the 'Consumer API Key' of your app to Life360 plugin setting page - 'TomTom API Key' field.
Remember, you have 2.500 daily API calls limit for free... When you are at 'Home', there are no API calls to TomTom.