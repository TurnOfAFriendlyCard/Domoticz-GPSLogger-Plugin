import Domoticz
import urllib.request, urllib.parse
from urllib.error import URLError, HTTPError
import json

class tomtomapi:
    rgeocodeaddr = "https://api.tomtom.com/search/2/reverseGeocode/%s,%s.json?key=%s"
    trafficaddr = "https://api.tomtom.com/routing/1/calculateRoute/%s:%s/json?traffic=true&avoid=unpavedRoads&travelMode=car&key=%s"

    def __init__(self):
        return

    def make_request(self, type, url):
        headers = {
            'Accept': 'application/json','User-Agent' : 'Domoticz/1.0'
        }
        request = urllib.request.Request(url, headers=headers)
        try:
            r = urllib.request.urlopen(request)
        except HTTPError as e:
            Domoticz.Log('TomtomAPI HTTPError Code: '+ str(e.code))
            retstatus = 1
            jsonr='Error'
        except URLError as e:
            Domoticz.Log('TomtomAPI URLError Reason: '+ str(e.reason))
            retstatus = 1
            jsonr='Error'
        else:
            jsonj = json.loads(r.read().decode('utf-8'))
            if type == 0:
                jsonr = jsonj['addresses'][0]['address']['freeformAddress']
                retstatus = 0
            elif type == 1:
                jsonr = jsonj["routes"][0]["summary"]['travelTimeInSeconds']
                retstatus=0
                Domoticz.Debug('Seconds:'+str(jsonr))
        return retstatus,jsonr

    def getaddress(self,apikey,lat,lon):
        url=self.rgeocodeaddr % (str(lat),str(lon),str(apikey))
        Domoticz.Debug('Address URL:'+url)
        stat, req = self.make_request(type=0,url=url)
        Domoticz.Debug('TStat Addr:'+str(stat))
        Domoticz.Debug('TReq Addr:'+str(req))
        return stat,req

    def getdistance(self,apikey,lat1,lon1,lat2,lon2):
        url = self.trafficaddr % (str(lat1)+','+str(lon1),str(lat2)+','+str(lon2),str(apikey))
        Domoticz.Debug('Distance URL:'+url)
        stat, dist = self.make_request(type=1,url=url)
        Domoticz.Debug('TStat Dis:'+str(stat))
        Domoticz.Debug('TReq Dis:'+str(dist))
        return stat,dist
