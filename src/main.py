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
    Fetch device devices seen in the last 2 hours.
    '''
    seen = []
    warnings.simplefilter('ignore',InsecureRequestWarning)
    raw_data = CLIENT.query(online_query)
    devices_online = list(raw_data.get_points())
    packages = len(devices_online) - 1
    i = 0
    while i <= packages:
        deveui = devices_online[i]["deveui"].replace("-", "").upper()
        seen.append(deveui)
        i += 1
    return seen


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
    #list of all valid deveuis
    with requests.Session() as sensors:
        response = sensors.get(csv_url)
        response = response.content.decode('utf-8')
        response = csv.reader(response.splitlines(), delimiter=',')
        response = list(response)
        response.pop(0)
    #Create update object for each device
    for deveui in response:
        updated = status(deveui[0], seen)
        objects.append(updated)


main()
