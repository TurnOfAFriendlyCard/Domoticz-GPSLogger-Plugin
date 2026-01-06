--
-- (C) marathon2010, last change 29-Dec-25
--
function determineToShow (domoticz, logType)
--         local logTypeToApply = domoticz.devices(domoticz.variables('LogMessageTypes').value).state
         local toPrint = false
--         if logTypeToApply == "Low"                                                                          then toPrint = true end         
--         if logTypeToApply == "Medium" and (logType == "medium" or logType == "high" or logType == "always") then toPrint = true end
--         if logTypeToApply == "High"   and (                       logType == "high" or logType == "always") then toPrint = true end
--         if logTypeToApply == "Always" and                                              logType == "always"  then toPrint = true end
         toPrint = true
         return toPrint
end

function printMessage (domoticz, messageToPrint, logType)
         if determineToShow (domoticz, logType) == true then print (messageToPrint) end
end

function roundValue(valueToRound, numberDecimals)
         valueToRound = valueToRound * (10 ^ numberDecimals)
         valueToRound = math.floor(valueToRound + 0.5)
         valueToRound = valueToRound / (10 ^ numberDecimals)
         return valueToRound
end

function writeFile(domoticz, fn, fnw, currentLat, currentLon)
   -- check significant changes in movement
   local numberDecimals = 3
   local roundedLat = roundValue(currentLat, numberDecimals)
   local roundedLon = roundValue(currentLon, numberDecimals)
   if (tostring(domoticz.data.PreviousLatitude) == tostring(roundedLat)) and (tostring(domoticz.data.PreviousLongitude) == tostring(roundedLon)) then
      printMessage (domoticz, "GPX: no changes Lat previous="..domoticz.data.PreviousLatitude.." current="..roundedLat.." Lon previous="..domoticz.data.PreviousLongitude.." current="..roundedLon, "low")
   else
   -- append latitude and longitude to the tracksfile in GPX format
      printMessage (domoticz, "GPX: to write.", "low")
      local f = io.open(fn, "a")
      f:write('    <rtept lat="')
      f:write(currentLat)
      f:write('" lon="')
      f:write(currentLon)
      f:write('"></rtept>')
      f:write("\n")
      f:close()
 
      domoticz.data.PreviousLatitude  = roundedLat
      domoticz.data.PreviousLongitude = roundedLon
      printMessage (domoticz, "GPX: check Lat previous="..domoticz.data.PreviousLatitude.." current="..roundedLat.." Lon previous="..domoticz.data.PreviousLongitude.." current="..roundedLon, "low")
      printMessage (domoticz, "GPX: written. Value frequency "..domoticz.data.waypointFrequency, "low")
   
      if domoticz.data.waypointFrequency == 0 then
         domoticz.data.waypointFrequency = 5
         -- append latitude and longitude including date/time to the waypointsfile in GPX format
         printMessage (domoticz, "GPX: to write waypoint. Value frequency "..domoticz.data.waypointFrequency, "low")
         local fw = io.open(fnw, "a")
         fw:write('  <wpt lat="')
         fw:write(currentLat)
         fw:write('" lon="')
         fw:write(currentLon)
         fw:write('"> <name>')
         fw:write(os.date("%d-%b-%Y %X"))
         fw:write('</name></wpt>')
         fw:write("\n")
         fw:close()
         printMessage (domoticz, "GPX: written waypoint.", "low")
      else
         domoticz.data.waypointFrequency = domoticz.data.waypointFrequency - 1
         printMessage (domoticz, "GPX: no waypoint written. Value frequency "..domoticz.data.waypointFrequency, "low")
      end
   end
end

function parseLine(line)
   local result = {}
   local from = 1
   local sep = ";"
   local field
   while true do
      local start, finish = string.find(line, sep, from)
      if not start then
         table.insert(result, string.sub(line, from))
         break
      end
      field = string.sub(line, from, start - 1)
      table.insert(result, field)
      from = finish + 1
   end
   return result[1], result[2]
end

return
{  active  = false
,  on      = {devices = {'Location - User RawData'
                        ,'Location - Generate GPX'
                        }
             }
,  data    = {waypointFrequency = { initial = '0' }
             ,PreviousLatitude  = { initial = '0' }
             ,PreviousLongitude = { initial = '0' }
             }
,  execute = function(domoticz, item)
      if item.isDevice then
         local pathFile      = "userdata/data/"
         local tracksFile    = pathFile.."TrackFromDomoticz.gpx"
         local waypointsFile = pathFile.."WaypointsFromDomoticz.gpx"
         if item.name == 'Location - Generate GPX' then
            if item.state == "On" then
--             create new tracks file
               printMessage (domoticz, "GPX: to initiate.", "low")
               local f = io.open(tracksFile , "w")
               f:write('<gpx version="1.1" creator="https://github.com/TurnOfAFriendlyCard/Domoticz-GPSLogger-Plugin">')
               f:write("\n")
               f:write("  <rte><name>GPS</name>")
               f:write("\n")
               f:close()
--             create new waypoint file, at closure will be included in the tracksfile
               local f = io.open(waypointsFile , "w")
               f:close()
               domoticz.data.waypointFrequency = 0                             -- once every frequency number the waypoint will be stored.
               domoticz.data.PreviousLatitude  = 0                             -- for checking relevent movement changes.
               domoticz.data.PreviousLongitude = 0                             -- for checking relevent movement changes.
               printMessage (domoticz, "GPX: initiated.", "always")
            else
               printMessage (domoticz, "GPX: to close.", "low")
               local f = io.open(tracksFile , "a")
               local fw = io.open(waypointsFile , "r")
               f:write("  </rte>")
               f:write("\n")
--             read all waypoints and append to tracks file
               local waypointsContent = fw:read("*all")
               f:write(waypointsContent)
               f:write("</gpx>")
               f:close()
               fw:close()
               os.rename(tracksFile, pathFile.."Track_"..os.date("%d_%b_%Y_%H%M")..".gpx")
               os.remove(waypointsFile)
               printMessage (domoticz, "GPX: closed.", "always")
            end
         else
            if domoticz.devices('Location - Generate GPX').state == "On" then
               local currentLat, currentLon = parseLine(item.sValue)
               writeFile(domoticz, tracksFile, waypointsFile, currentLat, currentLon)
            end
         end
      end
   end
}
