from ansible.plugins.inventory import (
    BaseInventoryPlugin,
    Constructable,
    expand_hostname_range,
    detect_range,
)
import requests
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class NetBrainsAPI:
    def __init__(self):
        self.api_url = "https://netbrains.com/ServicesAPI/API/V1"
        self.token = None

    def login(self, username, password):
        # POST /Session
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        body = {
            "username": username,
            "password": password
        }
        full_url = self.api_url + "/Session"
        try:
            # Do the HTTP request
            response = requests.post(full_url, headers=headers, data = json.dumps(body), verify=False)
            # Check for HTTP codes other than 200
            if response.status_code == 200:
                # Decode the JSON response into a dictionary and use the data
                js = response.json()
                self.token = js["token"]
                return True
            else:
                return False
        except Exception as e:
            print (str(e))
            return False

    def logout(self):
        # DELETE /Session
        if self.token is not None: # If we have a token, then we are logged in
            full_url = self.api_url + "/Session"
            # Set proper headers
            headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
            headers["token"] = self.token

            try:
                # Do the HTTP request
                response = requests.delete(full_url, headers=headers, verify=False)
                # Check for HTTP codes other than 200
                if response.status_code == 200:
                    # Decode the JSON response into a dictionary and use the data
                    js = response.json()
                    return True
                else:
                    print ("Session logout failed! - " + str(response.text))
                    return False
            except Exception as e:
                print (str(e))
                return False

    def get_devices(self):
        full_url = self.api_url + "/CMDB/Devices"
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        headers["Token"] = self.token

        try:
            # response = requests.get(full_url, headers=headers, verify=False)
            # if response.status_code == 200:
                # result = response.json()
                return {
                    "devices": [
                        {
                            'id': 'ad53a0f6-644a-400b-9216-8df746baed3b',
                            'mgmtIP': '10.1.12.2',
                            'hostname': 'Client1',
                            'deviceTypeName': 'Cisco Router',
                            'firstDiscoverTime': '0001-01-01T00:00:00', 
                            'lastDiscoverTime': '0001-01-01T00:00:00'
                        }
                    ]
                }
                # return result
            # else:
                # return False
        except Exception as e:
            print (str(e)) 
            return False

    def get_device(self, device_id):
        pass

    def get_device_attributes(self, device_hostname, attribute_name=None):
        hostname = device_hostname

        body = {
            "hostname": hostname, 
        }

        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        headers["Token"] = self.token
        full_url= self.api_url + "/CMDB/Devices/Attributes"

        if attribute_name is not None:
            body.attributeName = attribute_name

        try:
            # response = requests.get(full_url, params=body, headers=headers, verify=False)
            # if response.status_code == 200:
                # result = response.json()
                return {
                    "hostname": "Client1",
                    "attributes": {
                        "name": "Client1",
                        "mgmtIP": "123.20.20.20",
                        "mgmtIntf": "Loopback0",
                        "subTypeName": "Cisco Router",
                        "vendor": "Cisco",
                        "model": "DEVELOPMENT TEST SOFTWARE",
                        "ver": "15.4(2)T4",
                        "sn": "71372834",
                        "site": "My Network\\Unassigned",
                        "loc": "",
                        "contact": "",
                        "mem": "356640420",
                        "assetTag": "",
                        "layer": "",
                        "descr": "",
                        "oid": "1.3.6.1.4.1.9.1.1",
                        "driverName": "Cisco Router",
                        "assignTags": "",
                        "hasBGPConfig": True,
                        "hasOSPFConfig": False,
                        "hasEIGRPConfig": False,
                        "hasISISConfig": False,
                        "hasMulticastConfig": False,
                        "TestTable": "",
                        "newAttribute": "20",
                        "attributeName": ""
                    },
                    "statusCode": 790200,
                    "statusDescription": "Success."
                }
                # return result
            # else:
                # print ("Get device attributes failed! - " + str(response.text))
                # return False
        except Exception as e:
            print (str(e))
            return False

class InventoryModule(BaseInventoryPlugin, Constructable):

    NAME = "netbrains"

    def verify_file(self, path):
        """ return true/false if this is possibly a valid file for this plugin to consume """
        valid = False
        if super(InventoryModule, self).verify_file(path):
            if path.endswith(
                ("netbrains.yaml", "netbrains.yml")
            ):
                valid = True
        return valid
    

    def parse(self, inventory, loader, path, cache=True):
        super(InventoryModule, self).parse(inventory, loader, path, cache)

        config = self._read_config_data(path)
        # strict = self.get_option("strict")

        # Initialize the NetBrains API client, and try to login
        netbrains_client = NetBrainsAPI()
        # logged_in = netbrains_client.login(config["username"], config["password"])

        # if not logged_in:
            # raise Exception("Login failed!")
    
        devices = netbrains_client.get_devices()
        
        if not devices:
            raise Exception("Failed to get devices from NetBrains API")
        
        for device in devices["devices"]:
            device_attributes = netbrains_client.get_device_attributes(device["hostname"])["attributes"]

            if not device_attributes:
                raise Exception("Failed to get device attributes from NetBrains API")
            
            self.inventory.add_host(device["hostname"])
            self.inventory.set_variable(device["hostname"], "ansible_host", device["mgmtIP"])
            self.inventory.set_variable(device["hostname"], "subTypeName", device_attributes["subTypeName"])
            self.inventory.set_variable(device["hostname"], "vendor", device_attributes["vendor"])
            self.inventory.set_variable(device["hostname"], "model", device_attributes["model"])
            self.inventory.set_variable(device["hostname"], "site", device_attributes["site"])
            self.inventory.set_variable(device["hostname"], "loc", device_attributes["loc"])
