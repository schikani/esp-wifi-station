import time
from ubrainDB import ubrainDB as DB
from network import *
from time import sleep

class Station():

    database_name = ".networks"
    database = DB(database_name)
    known_networks = "known_networks"
    access_point = "access_point"
    prompt = "<:> "

    def __init__(self):
        if not self.check_if_key_exist(self.known_networks):
            self.create_database(self.known_networks)
        
        if not self.check_if_key_exist(self.access_point):
            self.create_database(self.access_point)

        self.station = WLAN(STA_IF)
        self.ap_station = WLAN(AP_IF)
        self.ap_station.active(True)
        self.station.active(True)
        self.num_of_reconnects_while_connecting(10)
        self.ap_station.config(essid=self.database.read(self.access_point)[0])
        self.ap_station.config(max_clients=self.database.read(self.access_point)[1])
        self.func_on_connect = lambda x: x if self.is_connected() else "Can't connect to internet!"

    def disconnect(self):
        self.station.disconnect()
        
        
    def create_database(self, key):
        if key == self.known_networks:
            self.database.write(self.known_networks, {})
        elif key == self.access_point:
            self.database.write(self.access_point, ["MicroPython", 5])

    def verbose(self, val):
        self.database.verbose(val)

    def num_of_devices_connected_to_ap(self):
        try:
            return len(self.ap_station.status("stations"))
        except:
            return 0

    def num_of_reconnects_while_connecting(self, val):
        self.station.config(reconnects=val)

    def is_connected(self):
        return self.station.isconnected()

    def ifconfig(self):

        ssid = ""
        ip = ""
        rssi_percent = 0

        try:
            ssid =  self.station.config('essid')
            ip = self.station.ifconfig()
            rssi_percent = self.get_signal_percent(self.station.status("rssi"))
        except:
            pass

        return ssid, ip, rssi_percent

    def disable_mode(self, ap_station=False, station=False):
        if ap_station:
            self.ap_station.active(False)
        
        if station:
            self.station.active(False)

    def enable_mode(self, ap_station=False, station=False):
        if ap_station:
            self.ap_station.active(True)
        
        if station:
            self.station.active(True)

    def add_network(self, ssid, password):
        ssid = ssid.encode("utf8")
        password = password.encode("utf8")
        networks_dict = self.database.read(self.known_networks)
        networks_dict[ssid] = password
        self.database.write(self.known_networks, networks_dict)

    def delete_network(self, ssid):
        _temp_dict = self.database.read(self.known_networks)
        if ssid in _temp_dict.keys():
            _temp_dict.pop(ssid)
        self.database.write(self.known_networks, _temp_dict)

    def get_known_networks(self):
        return self.database.read(self.known_networks)

    def set_access_point(self, ap_ssid, max_clients):
        access_point_list = []
        access_point_list.append(ap_ssid)
        access_point_list.append(max_clients)
        self.database.write(self.access_point, access_point_list)
        self.ap_station.config(essid=ap_ssid)
        self.ap_station.config(max_clients=max_clients)

    def get_signal_percent(self, val):
        return min((val + 100) * 2, 100)

    def scan_for_networks(self):
        self.disable_mode(station=True)
        sleep(0.2)
        self.enable_mode(station=True)
        netwrks = self.station.scan()

        ssids = []
        rssi = []

        for item in range(len(netwrks)):
            ssids.append(netwrks[item][0].decode("utf8"))
            rssi_percent = self.get_signal_percent(netwrks[item][3])
            rssi.append(rssi_percent)

        return ssids, rssi

    def check_if_key_exist(self, key):
        if self.database.read(key) != "Invalid key!":
            return 1
        return 0

    def check_status(self, code):

        status = ""

        if code == STAT_IDLE:
            status = "IDLE"
        
        elif code == STAT_CONNECTING:
            status = "CONNECTING"

        elif code == STAT_WRONG_PASSWORD:
            status = "WRONG PASSWORD"

        elif code == STAT_NO_AP_FOUND:
            status = "NO NETWORK REPLIED"
        
        elif code == STAT_ASSOC_FAIL:
            status = "ASSOC FAIL"

        elif code == STAT_GOT_IP:
            status = "CONNECTED"
        
        return status

    def manually_connect(self, ssid):
        if isinstance(ssid, str):
            ssid = ssid.encode("utf8")

        if ssid in self.database.read(self.known_networks).keys():
            print("Found: '{}' in the database".format(ssid.decode("utf8")))
            if self.is_connected():
                if ssid.decode("utf8") != self.ifconfig()[0]:
                    self.disconnect()
                    print("Connecting...")
                    self.station.connect(ssid, self.database.read(self.known_networks)[ssid])
                else:
                    print("Already connected to '{}'".format(ssid.decode("utf8")))
            else:
                print("Connecting...")
                self.station.connect(ssid, self.database.read(self.known_networks)[ssid])

            while self.station.status() == STAT_CONNECTING:
                pass
            print("status_code: {}".format(self.station.status()))
            if self.is_connected():
                print(self.ifconfig())
            else:
                print("Connection unsuccessful!")
        else:
            print("'{}' can't be found in the database".format(ssid))

    def auto_connect(self):
        ntwks = self.scan_for_networks()
        knwn_ntwks = self.database.read(self.known_networks).keys()
        if len(list(knwn_ntwks)) == 0:
            print("No saved network/s found in the database")
            return 0
        _temp_dict = {}
        _sort_by_db = []
        for index, item in enumerate((ntwks[0])):
            if item.encode("utf8") in knwn_ntwks:
                print("Found: '{}' on the radar".format(item))
                _temp_dict[ntwks[1][index]] = ntwks[0][index].encode("utf8")
                _sort_by_db.append(ntwks[1][index])
        _sort_by_db.sort(reverse=True)
        for i in _sort_by_db:
            print("Connecting to '{}'".format(_temp_dict[i].decode("utf8")))
            self.station.connect(_temp_dict[i],
            self.database.read(self.known_networks)[_temp_dict[i]])
            while self.station.status() == STAT_CONNECTING:
                pass   
            print("status_code: {}".format(self.station.status()))
            if self.is_connected():
                print(self.ifconfig())
                break
            else:
                print("Can't connect to network: '{}'".format(_temp_dict[i].decode("utf8")))
                
        if not self.is_connected():
            print("Connection unsuccessful!")

    def _ui_ap_station(self):
        print("Please enter ap_ssid")
        inp1 = input(self.prompt)
        print("Please enter max_allowed_clients (max ~ 10)")

        try:
            inp2 = int(input(self.prompt))

        except ValueError:
            pass

        self.set_access_point(inp1, inp2)

        return "Access point created with name: '{}' | max_allowed_clients: '{}'".format(inp1, inp2)

    def _ui_network_sig_strength(self, val):
        signal = ""

        if val == 0:
            signal = "....."
        
        elif val <= 20:
            signal = "#...."
        
        elif 20 < val <= 40:
            signal = "##..."
        
        elif 40 < val <= 60: 
            signal = "###.."

        elif 60 < val <= 80:
            signal = "####."

        elif 80 < val <= 100:
            signal = "#####"

        
        return signal


    def _ui_radar(self):
        network_tuple = self.scan_for_networks()
        print("Enter the index number associated with the network to add it\n")
        _temp_dict = {}
        for i in range(len(network_tuple[0])):
            _temp_dict[i] = network_tuple[0][i]
            print("[%s] %s    | %s %s"
            % (i + 1, network_tuple[0][i],
             self._ui_network_sig_strength(network_tuple[1][i]),
             network_tuple[1][i]), "%")
            
        if len(_temp_dict) == 0:
            print("No available networks found in the area")
        
        else:
            try:
                inp1 = int(input(self.prompt))
                print("Enter password for '{}'".format(_temp_dict[inp1-1]))
                inp2 = input(self.prompt)
                self.add_network(_temp_dict[inp1-1], inp2)
                print("Network '{}' is added to the database successfully!".format(_temp_dict[inp1-1]))
            except ValueError:
                pass


    def _ui_manually_connect(self):
        print("Enter the index number associated with the network to connect\n")
        _temp_dict = {}
        for index, item in enumerate(self.database.read(self.known_networks).keys()):
            _temp_dict[index] = item
            print("[{}] {}".format(index+1, item.decode("utf8")))
        try:
            inp1 = int(input(self.prompt))
            self.manually_connect(_temp_dict[inp1-1])

        except ValueError:
            pass


    def _ui_add_network(self):
        print("Enter ssid")
        inp1 = input(self.prompt)
        print("Enter password")
        inp2 = input(self.prompt)
        self.add_network(inp1, inp2)


    def _ui_delete_network(self):
        print("Enter the index number associated with the network to delete\n")
        _temp_dict = {}
        for index, item in enumerate(self.database.read(self.known_networks).keys()):
            _temp_dict[index] = item
            print("[{}] {}".format(index, item.decode("utf8")))
        try:
            inp1 = int(input(self.prompt))
            self.delete_network(_temp_dict[inp1-1])

        except ValueError:
            pass

    def help(self):
        message = """
        __|_________________________________________________________|__
        |                * Welcome to the Station! *              |
        |                                                         |
        |    * Type any below given commands and press Enter *    |
        |         * Just press Enter to exit the station *        |
        |                                                         |
        |    <:> "AP" to configure access point settings          |
        |    <:> "R" to start the radar                           |
        |    <:> "MC" to manually connect to a saved network      |
        |    <:> "DC" to disconnect from a network                |
        |    <:> "A" to add a new network                         |
        |    <:> "D" to remove a network                          |
        |    <:> "H" to open this help                            |
        |_________________________________________________________|"""

        print(message)

    def interrupt_on_connect(func):
        pass

    def ui(self):
        commands = {
        "ap": self._ui_ap_station,
        "r": self._ui_radar,
        "mc": self._ui_manually_connect,
        "a": self._ui_add_network,
        "d": self._ui_delete_network,
        "dc": self.disconnect,
        "h": self.help
        }
        ui = """
        _________________________________________
        CONNECTED STATION NAME: {} 
        SIGNAL: |{}|{}% 
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ACCESS POINT NAME: {}
        NUM OF DEVICES CONNECTED: {}
        _________________________________________"""
        

        while True:
                 
            ssid = self.ifconfig()[0]
            network_bar = self._ui_network_sig_strength(self.ifconfig()[2])
            signal_strength = self.ifconfig()[2]
            access_point_name = self.database.read(self.access_point)[0]
            devices_connected = self.num_of_devices_connected_to_ap()

            ui = ui.format(ssid, network_bar, signal_strength, access_point_name, devices_connected)
            print(ui)
            cmd = input(self.prompt)
            cmd = cmd.lower()
            if cmd == "":
                break

            if cmd in commands.keys():
                commands[cmd]()

                
