import csv
import influxdb
import warnings
import requests
import configparser
from requests.packages.urllib3.exceptions import InsecureRequestWarning


CONF_FILE = "settings.conf"
config = configparser.ConfigParser()
config.read(CONF_FILE)

DB_USER = config.get("info", "user")
DB_PASS = config.get("info", "pass")
DB_HOST = config.get("info", "host")
DB_DEFAULT = config.get("info", "db_default")
DB_PORT = config.get("HTTP", "port")
CLIENT = influxdb.InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_DEFAULT)

csv_url = config.get("URL", "all")
online_query = config.get("Query", "deveuis")


def check_devices():
    '''
    Fetch devices seen in the last 2 hours.
    '''
    seen = []
    warnings.simplefilter('ignore',InsecureRequestWarning)
    raw_data = CLIENT.query(online_query)
    devices_online = list(raw_data.get_points())
    for device in devices_online:
        deveui = device["deveui"].replace("-", "").upper()
        if deveui not in seen:
            seen.append(deveui)
    return seen

def valid_deveuis():
    '''
    Return a list of all devices we have

    Fetches static-sensors/all.csv or other configured .csv using http
    '''
    deveuis = []
    with requests.Session() as sensors:
        response = sensors.get(csv_url)
        content = response.content.decode('utf-8')
        reader = csv.reader(content.splitlines(), delimiter=',')
        deveuis = list(reader)
    deveuis.pop(0)
    deveuis = [line[0] for line in deveuis]
    return deveuis


def status(deveui, seen):
    '''
    Check if sensor has been seen in the last 2h.
    '''
    update_status = {}
    update_status["_id"] = deveui
    update_status["update"] = {}
    if deveui in seen:
        status = "online"
    else:
        status = "offline"
    update_status["update"]["status"]  = status
    return update_status

def main():
    objects = []
    seen = check_devices()
    valid = valid_deveuis()
    # Create update object for each device
    for deveui in valid:
        updated = status(deveui, seen)
        objects.append(updated)

main()
