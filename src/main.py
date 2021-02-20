import csv
import warnings

import configparser
import influxdb
import requests

from requests.packages.urllib3.exceptions import InsecureRequestWarning


CONF_FILE = "settings.conf"
config = configparser.ConfigParser()
config.read(CONF_FILE)

DB_USER = config.get("InfluxDb", "user")
DB_PASS = config.get("InfluxDb", "pass")
DB_HOST = config.get("InfluxDb", "host")
DB_DEFAULT = config.get("InfluxDb", "db_default")
DB_PORT = config.get("InfluxDb", "port")
CLIENT = influxdb.InfluxDBClient(DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_DEFAULT)

SC_ENDPOINT = config.get("SmartCampusApi", "url").rstrip("/")
# Optional ApiKey obtained from the api. If key is None, skip authenticated requests.
SC_APIKEY = config.get("SmartCampusApi", "apikey") or None
if not SC_APIKEY:
    warnings.warn("Updating sensors is disabled, as apikey is not specified in settings")

csv_url = config.get("URL", "all")
online_query = config.get("Query", "deveuis")


def smart_campus_devices():
    '''
    Fetch all devices from the Smart Campus Api.

    Returns:
        List of device objects.

    Raises:
        RuntimeError: Bad response or no devices.
    '''
    response = requests.get(F"{SC_ENDPOINT}/devices/listAll")
    if response.status_code != 200:
        content = response.content.decode("utf-8")
        raise RuntimeError(F"Smart Campus API responded with status {response.status_code}: {content}")
    devices = response.json()
    if not isinstance(devices, list) or devices == []:
        raise RuntimeError("Smart Campus API didn't respond with devices.")
    return devices

def smart_campus_update(_id, status):
    '''
    Update a sensor's status by sending a POST-request to the Smart Campus API.

    Args:
        _id: smart campus device document _id
        status: status string

    Returns:
        None

    Raises:
        RuntimeError: Device couldn't be updated.
    '''
    if not SC_APIKEY:
        return

    headers = {"Authorization": F"Api-Key {SC_APIKEY}"}
    update = {"status": status}
    data = {"_id": _id, "update": update}

    response = requests.post(F"{SC_ENDPOINT}/devices/update", json=data, headers=headers)
    if response.status_code != 200:
        content = response.content.decode("utf-8")
        raise RuntimeError(F"Smart Campus API responded with status {response.status_code}: {content}")

    response_json = response.json()
    if not isinstance(response_json, dict):
        raise RuntimeError("Device update got bad response from Smart Campus API.")
    if "success" not in response_json or not response_json["success"]:
        message = response_json["msg"] if "msg" in response_json else ""
        raise RuntimeError(F"Device update failed: {message}")


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
    Return a list of all devices we have.

    Fetches static-sensors/all.csv or other configured .csv using http.
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
