## GOAL
Capture location data obtained via GPSLogger app and present in Domoticz devices.

## DESCRIPTION
A mobile phone is used to capture actual location data. The app used for this plugin is `GPSLogger`,
however other GPS logging apps can be used as well. In fact the most important prerequisite is that the
app is able to share location data via the `Domoticz API` on regular basis.

Concept is that `users` are determined for these mobile phones (just names, no formal users in Domoticz).
Besides that the `home location` is identified by the location setup in Domoticz. A `fence` around the home
location determines how Home is identified. For example a circle of 100 meters around the address
`Coolsingel 40, Rotterdam, the Netherlands` (latitude `51.922710` and longitude `4.479160`).

Multiple mobile phones are able to have connection with Domoticz, so in fact a `community circle`
can be setup for logging data and processing that data into Domoticz. For instance triggers in Domoticz
can be build to switch of the lights when all mobile phone users left the house. Or switch on when one of the
mobile phone users arrive at home. Or the alarm system can be triggered (switch on when all mobile phone users
left the house and switch off when one mobile phone users arrives at home).

Next devices will be created and updated in Domoticz (in the utility tab unless otherwise specified):
1. `Presence`: This is an On/Off switch indicating the user is within the fence (in switches tab).
2. `Location`: Text describing what the actual location of the user is.
3. `Battery`:  Charging percentage of the battery of the user.
4. `Distance`: Distance in minutes of the actual location to the fence (to implement in future).
5. `Speed`:    Speed in kilometers / hour of the user.
6. `RawData`:  Data which is captured from the GPSLogger app. This device is hidden (only in devices tab).

## INSTALLATION / SETUP
### A. Plugin
1. Open a `PuTTY` session.
2. In the session go to the `Plugin` folder of Domoticz.
3. Download the Plugin: `git clone https://github.com/TurnOfAFriendlyCard/Domoticz-GPSLogger-Plugin`
4. Alternative is to download and extract the zip file:
   - Go to https://github.com/TurnOfAFriendlyCard/Domoticz-GPSLogger-Plugin
   - Click on Code and select Download ZIP.
   - Create a folder for the plugin (`mkdir Domoticz-GPSLogger`) in the `Plugin` folder of Domoticz.
5. Go to folder (`cd Domoticz-GPSLogger`).
6. Make the plugin.py file executable (`chmod 755 plugin.py`).
7. Restart Domoticz.

### B. Domoticz
1. In the hardware tab a new `type` will be available: `GPS Logger Presence`.
2. Create the new hardware:
   - Enter a logical name (for instance `Location`). Will be a prefix to all devices created.
   - Select the hardware type `GPS Logger Presence`.
   - Enter the names of each user of the mobile phones. Just logical names, not a Domoticz username. Separate with semicolons.
   - Enter the fence size in meters of the Home location. Within this fence Home is determined.
   - Select the map providor (either `Open Streetmap` or `TomTom`).
      - For `TomTom` obtain an API key (see History on how-to).
   - When required debug message can be shown in the Domoticz log (set Debug on True).
   - Press Add to complete the installation.
4. Devices as summarized above will be created and plugin will be started.
5. Determine the `Idx` number in the devices tab for the `RawData` devices. These are required for GPSLogger setup.
6. Create a specific Domoticz user for the GPSLogger integration (that user will populate the `RawData` devices). Rights `User` and Active Menu `none`. No devices need to be set.

### C. Encode username/password
1. Go to the website https://www.base64encode.org/ to encode username and password into Base64 format.
2. Click on Encode.
3. Enter `username`:`password` into the text box. This the username/password defined in step B5. Also include the **colon** as separation between username and password.
4. So the text would look like `LocUser:LocPWD1234` where **LocUser** is the `username` and **LocPWD1234** is the `password`.
5. Output is something like `TG9jVXNlcjpMb2NQV0QxMjM0` (the example in step 4 should give the exact same result).

### D. GPSLogger
The Android app `GPSLogger` is described at https://gpslogger.app/. Installation of the app is via `F-Droid` (Free and Open Source Software).
1. Open a webbrowser on the mobile phone.
2. Go to https://f-droid.org/
   - Click on `Download F-Droid`.
   - Once download is completed, open the F-Droid.apk.
   - Install the F-Droid app.
3. Open F-Droid app.
   - Message will appear `application sources will be updated`.
4. Click on the `green search glass` in the bottom right-corner.
5. In the search bar on the top side of the screen enter `GPSLogger`.
6. Click on `Install` button to install the GPSLogger app.
7. Open GPSLogger app (vs 129 was used during plugin v2.0.0 development).
8. Approve authorizations (location, files/photo's and battery background).
9. In `Logging details` switch on "Log to custom URL" and switch off "Log to GPX".
10. In `Performance` set "Logging Interval" to for instance 15 seconds (so data is shared to Domoticz by this interval).
11. In `Custom URL` switch on "Log to custom URL" (should be switched on already).
12. Click on `URL` and enter `servername`, `port` and `body`. Should look like this
   - `https://example.com:443/json.htm?type=command&param=udevice&idx=<Idx>&nvalue=0&svalue=%LAT;%LON;%SPD;%BATT`
   - For `<Idx>` enter the value determined in step B5.
13. Click on HTTP Headers and enter
 
   - `Content-Type: application/json`

   - `Authorization: Basic <base64>`

   - The value of `<base64>` is the value generated in step C5.
14. Click on `HTTP Method` and set value to **POST**.
15. If a secure connection is used, click on validate SSL certificate (will show pop-up).
16. On the main screen click `Start Logging`.
17. Data is now flowing from the GPSLogger app to the RawData device.
18. The GPSLogger can be closed, will run in the background.
19. Repeat these steps for every mobile phone involved. Take care to use different `Idx` numbers (step D12).

### E. Locations
The plugin comes with a file `locations.txt`. In this files you may define your own locations. Instead of showing the full address in the `location` device the shortname will be shown. The file may look like this (first line not to be changed or removed):

`Name,Latitude,Longitude,Radius`

`Town Hall Rotterdam,51.922710,4.479160,50`

Multiple lines for your own locations can be defined.

### HISTORY 
The concept is based on the `Life360 Plugin` by fibalci. This plugin is not maintained anymore and also deprecated.
He thanked Harper Reed for Python implementation of Life 360 API: https://github.com/harperreed/life360-python.

The icons are downloaded from `Free Vector Graphics` by www.Vecteezy.com.

`TomTom API key` is not required, but if you want to get current address of a member and driving distance,
you should get a TomTom API key and copy-paste here, otherwise leave it empty.

How to get a `TomTom API Key`:
- Go to https://developer.tomtom.com/user/register page.
- Create a new User Account.
- Login to your account and from `My Apps`,
   - press 'Add a new app' to add a new app and select at least 'Routing API' and 'Search API',
   - you can select all APIs here if you want.
- Then from the 'Keys' page, copy the 'Consumer API Key' of your app to plugin setting page - `TomTom API Key` field.
- Remember, you have 2.500 daily API calls limit for free... When you are at `Home`, there are no API calls to TomTom.
