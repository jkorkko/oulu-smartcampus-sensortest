import csv
import time
import json
import influxdb
import warnings
import requests
import datetime
import configparser
import urllib.request
from requests.packages.urllib3.exceptions import InsecureRequestWarning


devices_online = []
updated = []
json_objects = []

CONF_FILE = "settings.conf"
config = configparser.ConfigParser()
config.read(CONF_FILE)

DB_USER = config.get("info", "user")
DB_PASS = config.get("info", "pass")
DB_HOST = config.get("info", "host")
DB_DEFAULT = config.get("info", "db_default")
DB_PORT = config.get("HTTP", "port")
CLIENT = influxdb.InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_DEFAULT)

json_url = config.get("URL", "installed")
csv_url = config.get("URL", "all")
online_query = config.get("Query", "deveuis")
time_query = config.get("Query", "timestamp")


class update_sensor:
    #Static information commented out
    def __init__(self, deveui):

        #self.location = {
            #"_id": deveui,
            #"coordinates": "Not installed",
            #"type": "Point"
        #}

        self.update = {
            #"description": "Not installed",
            #"deviceId": deveui,
            #"deviceType": "Not available",
            #"floorLevel": "Not installed",
            "lastSeen": "-",
            #"location": self.location,
            #"image": "Not implemented",
            "status": "online"
        }

        self.info = {
            "_id": deveui,
            "update": self.update
        }


    def sensor_info(self, deveui, curr_time):
        '''
        Read and add data from json-file.
        '''
        try:
            devices_online.remove(deveui)
        except ValueError:
            #If sensor not online, get last seen value
            self.update["status"] = "offline"
            device_id = self.format_str(deveui)
            self.update["lastSeen"] = self.last_seen(device_id, curr_time)
        '''
        ***Static information***
        for i, device in enumerate(json_objects):
            if deveui in device["id"]:
                if device["type"] == "Other":
                    device["type"] = "Elsys ELT-2-HP"
                self.location["coordinates"] = device["location"]
                self.update["description"] = device["desc"]
                self.update["deviceType"] = device["type"]
                self.update["floorLevel"] = device["floor"]
                json_objects.pop(i)
                break
        '''
        self.save(self.info)

    
    def format_str(self, deveui):
        '''
        Format deveui compatible for query string
        '''
        move = 2
        device_id = deveui.lower()
        for index in range(7):
            device_id = device_id[:(index*2) + move] + "-" + device_id[(index*2) + move:]
            move += 1
        return device_id
            

    def last_seen(self, deveui, time_now):
        '''
        Calculate time elapsed from last received package.
        '''
        warnings.simplefilter('ignore',InsecureRequestWarning)
        try:
            sensor_seen = CLIENT.query(time_query.format("'" + deveui + "'"))
            sensor_seen = eval(str(sensor_seen)[39:-3])
            last_seen = datetime.timedelta(seconds = int(sensor_seen["last"]))
            if (time_now.days - last_seen.days) != 0:
                return ("{} day(s) ago".format(time_now.days - last_seen.days))
            else:
                if ((time_now.seconds - last_seen.seconds) // 3600) <= 24:
                    return( "{} hours ago".format((time_now.seconds - last_seen.seconds) // 3600))
                else:
                    return("{} day(s) ago".format((time_now.seconds - last_seen.seconds) // 86400))
        except SyntaxError:
            return("unavailable")
            

    def save(self, sensor_info):
        '''
        Save object.
        '''
        updated.append(sensor_info)


def check_devices():
    '''
    Fetch device devices seen in the last 2 hours.
    '''
    warnings.simplefilter('ignore',InsecureRequestWarning)
    raw_data = CLIENT.query(online_query)
    raw_data = eval(str(raw_data)[39:-3])
    for package in raw_data:
        if package["deveui"] not in devices_online:
            devices_online.append(package["deveui"].replace("-", "").upper())


def get_time():
    '''
    Get current epoch time.
    '''
    current_time = time.time()
    current_time = datetime.timedelta(seconds = current_time)
    return current_time


def main():
    check_devices()
    curr_time = get_time()
    #Get sensor info from json-file
    response = urllib.request.urlopen(json_url).read().decode("UTF-8")
    json_objects = response.splitlines()
    for i, json_object in enumerate(json_objects):
        json_object = eval(json_object)
        json_objects[i] = json_object
    #Make a list of all valid deveuis and check their status
    with requests.Session() as sensors:
        response = sensors.get(csv_url)
        response = response.content.decode('utf-8')
        response = csv.reader(response.splitlines(), delimiter=',')
        response = list(response)
        response.pop(0)
    #Create update object for each device
    for deveui in response:
        new_update = update_sensor(deveui[0])
        new_update.sensor_info(deveui[0], curr_time)
        

main()
