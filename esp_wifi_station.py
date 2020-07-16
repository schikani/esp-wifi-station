# Use this file with boot.py to start the esp_wifi_station in the beginning after boot.
# On every boot, the station attempts to auto-connect to a saved network if available.
# Use station() to call the station from the REPL.
import network
import uos
import machine
import uio
import ujson
import gc
import esp
import time

esp.osdebug(None)
gc.collect()

# Get Board info.
board_info = uos.uname()
board_name = board_info[0]

# Configuring some Global variables and the inbuilt timer.
tim = machine.Timer(-1)
TRIGGER = False
SSID_COUNT = True
SSID_SUCCESS = False
RADAR_SUCCESS = False

# WiFi configuration:
wlan = network.WLAN(network.STA_IF)

# Access point configuration:
ap = network.WLAN(network.AP_IF)
AP_ESSID = ""
AP_MAX_CLIENT = ""

# This is where your information will be stored:
mydb = "mydb.json"

# Here we try to read the settings from database for ap_settings and max_clients(in esp32).
try:
    ap_reader = uio.open(mydb, "r")
    data_ap = ujson.load(ap_reader)
    ap_es_ps = data_ap["ap_essid_password"]
    for s, p in ap_es_ps.items():
        AP_ESSID = s
        ap_password = p
        break
    if board_name == "esp8266":
        ap.config(essid=AP_ESSID, password=ap_password)
    if board_name == "esp32":
        ap.config(essid=AP_ESSID)
        m_c = data_ap["ap_settings"]["max_clients"]
        ap.config(max_clients=m_c)
        AP_MAX_CLIENT = m_c

    ap.active(True)
    wlan.active(True)


# If the database file doesn't exist resulting in OSError,
# A new file with default settings is created with a system reboot.
except OSError:

    print("No ap database found.")
    f_w = uio.open(mydb, "w")
    new_data = {
        "ssid": {
        },
        "password": {
        },
        "ap_essid_password": {
            "ESP_Station": "MicropythoN"
        },
        "ap_settings": {
            "max_clients": 1
        }
    }
    ujson.dump(new_data, f_w)
    f_w.close()
    print("""
        ----------------------------------------------------
                  Curently there is no database
        A new database will be created with a system reboot.
        ----------------------------------------------------
        """)
    time.sleep(6)
    machine.reset()
    wlan.active(True)


# no_ssid is defined to check if a SSID exists in the database or not.
def no_ssid():
    global SSID_COUNT
    SSID_COUNT = False
    file_r = uio.open(mydb, "r")
    data_no_ssid = ujson.load(file_r)
    file_r.close()
    if len(data_no_ssid["ssid"]) > 0:
        SSID_COUNT = True


# rdr is defined for scanning available wifi networks and showing them to the user.
def rdr(user_dict, show=False):
    wlan.active(False)
    time.sleep(1)
    wlan.active(True)
    indx = 0
    for item in wlan.scan():
        indx += 1
        index = str(indx)
        mkstr = str(item[0])
        strip = mkstr.strip('(b')
        strip1 = strip.strip("' '")
        data_rdr = {index: strip1}
        user_eyes = "[" + index + "] " + strip1
        if show:
            print(user_eyes)
        user_dict.update(data_rdr)
    global RADAR_SUCCESS
    RADAR_SUCCESS = True


# wlan_connect is defined for accepting ssid, password.
# It tries to connect the network for 10 times.
def wlan_connect(ssid, password):
    wlan.disconnect()
    attempt = 0
    print("connecting...")
    wlan.connect(ssid, password)
    time.sleep(2)
    while True:
        time.sleep(2)
        # It shows the connected network.
        if wlan.isconnected():
            print("")
            print('<>_<> ' + 'connected to:', ssid)
            print('<>_<> ' + 'network config:', wlan.ifconfig())
            print("")
            break

        if attempt == 6:
            print("still connecting...")

        if attempt == 8:
            print("one last try...")

        # When 10 tries are done, it breaks the while loop.
        if attempt == 10 and not wlan.isconnected():
            print("Having some network problem. Please try again later.")
            time.sleep(3)
            station()
            break

        if not wlan.isconnected():
            attempt += 1
            wlan.connect(ssid, password)
            time.sleep(3)


# do_append is defined to add ssid, password to the databse.
def do_append(ssid=""):
    f1 = uio.open(mydb, "r")
    flr = ujson.load(f1)
    f1.close()
    new_ssid = ""
    if ssid != "":
        new_ssid = ssid
    if ssid == "":
        print('Type SSID:')
        new_ssid = input("<:> ")

    while True:
        if new_ssid != "":
            print('Type PASSWORD for ' + new_ssid)
            new_password = input("<:> ")
            if new_password == "":
                print("A password cannot be empty!")
                time.sleep(2)
                continue

            # Here it checks if the network already exists in the database.
            if new_ssid in flr["ssid"].values() and new_password in flr["password"].values():
                print("""
                This network exists in the database.
                Returning back to station.
                """)
                time.sleep(3)
                station()
                break

            if new_password != "":
                file_w = uio.open(mydb, "w")
                flr["ssid"][str(len(flr["ssid"]) + 1)] = new_ssid
                flr["password"][str(len(flr["password"]) + 1)] = new_password
                ujson.dump(flr, file_w)
                file_w.close()
                print("Network " + new_ssid + " is added successfully!")
                time.sleep(3)
                station()
                break

        if new_ssid == "":
            print("Adding nothing. Returning back to station")
            time.sleep(2)
            station()
            break


# do_connect is defined to go through the lines of the database to find ssid, password.
def do_connect():
    no_ssid()
    f2 = uio.open(mydb, "r")
    f2r = ujson.load(f2)
    f2.close
    # rdr is used here to compare available networks with saved networks.
    d = {}
    rdr(d)

    if SSID_COUNT:
        common_networks = set(d.values()) & set(f2r['ssid'].values())
        if len(common_networks) > 0:
            ssid = list(common_networks)[0]
            print('found: ' + ssid)

            key_list = list(f2r['ssid'].keys())
            val_list = list(f2r['ssid'].values())

            password = f2r['password'][key_list[val_list.index(ssid)]]

            wlan_connect(ssid, password)

        if len(common_networks) == 0:
            print("""
            Sorry, no network on radar matches the saved networks.
            Returning to the station.
            """)
            time.sleep(4)
            station()
    if not SSID_COUNT:
        print("""
            There is no database with saved networks.
            Returning to the station.
                """)
        time.sleep(4)
        station()


# ssids is defined to show the saved ssids in the database.
def ssids(user_dict):
    no_ssid()
    f3 = uio.open(mydb, "r")
    f3r = ujson.load(f3)
    f3.close()

    user_eyes = []

    if SSID_COUNT:
        global SSID_SUCCESS
        SSID_SUCCESS = True
        for k, v in f3r['ssid'].items():
            ssid = v
            password = f3r['password'][k]
            data_ssids = {k: (ssid, password)}
            user_dict.update(data_ssids)
            user_eyes.append((int(k), ssid))

        user_eyes.sort()
        for itm in user_eyes:
            print("[" + str(itm[0]) + "] " + itm[1])

    if not SSID_COUNT:
        SSID_SUCCESS = False
        print("""
            There is no database with saved networks.
            Returning to the station.
                """)
        time.sleep(4)
        station()


# access_point is defined to let other devices connect to this station.
def access_point():
    ap_file = uio.open(mydb, "r")
    data_access_p = ujson.load(ap_file)
    ap_file.close()
    for a in data_access_p["ap_essid_password"].keys():
        existing_ap = a
        break
    print("An access point already exists named: " + existing_ap)
    print("""
    If you continue, it will overwrite the existing settings
    Do you want to continue? Type (Y/N)
    """)
    usr_in = input("<:> ")
    if usr_in in ("Y", "y"):
        print("Type a name for your device.")
        essid = input("<:> ")
        if essid != "":
            ap_file = uio.open(mydb, "w")
            if board_name == "esp8266":
                while True:
                    print("Type a PASSWORD for " + essid + "\n" +
                          "Note: the password should have 8 or more chars. ")
                    password = input("<:> ")
                    if len(password) >= 8:
                        data_access_p["ap_essid_password"] = {essid: password}
                        ujson.dump(data_access_p, ap_file)
                        ap_file.close()
                        print("Access point created!")
                        print("Your device is named: " + essid)
                        print("""
                        A system reboot is necessary for the changes to take place. 
                        Reboot now? Type (Y/N).
                        """)
                        inp = input("<:> ")
                        if inp in ("y", "Y"):
                            machine.reset()
                        else:
                            station()
                            break
                    if len(password) < 8:
                        print(
                            "The password is too short please try a different one.")
                        continue

            if board_name == "esp32":
                data_access_p["ap_essid_password"] = {essid: "None"}
                print("""
                Do you want to configure max clients?
                Type (Y/N)
                """)
                ask = input("<:> ")
                if ask in ("Y", "y"):
                    while True:
                        print("""
                        How many clients do you want to allow?
                        (maximum = 10)
                        """)
                        try:
                            max_cl = int(input("<:> "))
                            if 11 > max_cl > 0:
                                data_access_p["ap_settings"]["max_clients"] = max_cl
                                ujson.dump(data_access_p, ap_file)
                                ap_file.close()
                                print("Access point created!")
                                print("Your device is named: " + essid)
                                print(
                                    "Maximum clients are set to: " + str(max_cl))
                                print("")
                                print("""
                                A system reboot is necessary for the changes to take place. 
                                Reboot now? Type (Y/N).
                                """)
                                inp = input("<:> ")
                                if inp in ("y", "Y"):
                                    machine.reset()
                                else:
                                    station()
                                    break

                            else:
                                print(
                                    "Invalid input! Please type correct input between (1-10).")
                                continue
                        except ValueError:
                            print(
                                "Invalid input! Please type correct input between (1-10).")
                            continue
                else:
                    ujson.dump(data_access_p, ap_file)
                    ap_file.close()
                    print("Access point created!")
                    print("Your device is named: " + essid)
                    print("""
                    A system reboot is necessary for the changes to take place. 
                    Reboot now? Type (Y/N).
                    """)
                    inp = input("<:> ")
                    if inp in ("y", "Y"):
                        machine.reset()
                    else:
                        station()

        if essid == "":
            print("SSID field can't be empty, returning back to the station.")
            print("")
            time.sleep(3)
            station()

    else:
        print("No changes made.")
        time.sleep(3)
        station()


# remove_data is defined to remove existing data from the database.
def remove_data(user_in, dictk):
    no_ssid()
    f4 = uio.open(mydb, "r")
    data_rd = ujson.load(f4)
    f4.close()
    if SSID_COUNT and user_in in dictk:
        del data_rd["ssid"][user_in]
        del data_rd["password"][user_in]

        f4 = uio.open(mydb, 'w')
        counter1 = 0
        counter2 = 0
        update_ssid = {}
        update_password = {}

        for v in data_rd["ssid"].values():
            counter1 += 1
            update_ssid.update({str(counter1): v})
        for v in data_rd["password"].values():
            counter2 += 1
            update_password.update({str(counter2): v})

        data_rd["ssid"] = update_ssid
        data_rd["password"] = update_password
        ujson.dump(data_rd, f4)
        f4.close()
        print("Done.")
        time.sleep(3)
        station()
    if SSID_COUNT and not user_in in dictk:
        print("Incorrect input. Deleting nothing.")
        time.sleep(2)
        station()


# check is defined to start the timer after checking if network is not connected and the TRIGGER is False
# Please set your required time in period (in milliseconds).
def check():
    if not wlan.isconnected() and TRIGGER is False:
        tim.init(period=5000, mode=machine.Timer.ONE_SHOT,
                 callback=lambda t: check_again())


# check_again is defined to check again if any changes has happened with the conditions.
def check_again():
    if not wlan.isconnected() and TRIGGER is False:
        print("")
        print('<>_<> ' + 'Board type: ' + board_name)
        print('<>_<> ' + 'Discoverable as: ' + AP_ESSID)
        print('<>_<> ' + 'Network config:', ap.ifconfig())
        if AP_MAX_CLIENT != "":
            print('<>_<> ' + 'Maximum clients allowed: ' + str(AP_MAX_CLIENT))
        print("")
        print("Attempting auto-connection...")
        do_connect()


# station is defined to interact with the user.
def station():
    global TRIGGER
    TRIGGER = True
    global SSID_SUCCESS
    SSID_SUCCESS = False
    global RADAR_SUCCESS
    RADAR_SUCCESS = False

    print("""
  __|_________________________________________________________|__
    |                * Welcome to the Station! *              |
    |                                                         |
    |    * Type any below given commands and press Enter *    |
    |         * Just press Enter to exit the station *        |
    |                                                         |
    |    <:> "AP" to configure access point settings          |
    |    <:> "R" to start the radar                           |
    |    <:> "C" to auto-connect to a saved network           |
    |    <:> "MC" to manually connect to a saved network      |
    |    <:> "A" to add a new network                         |
    |    <:> "D" to remove a network                          |
    |_________________________________________________________|
    """)

    try:
        user_input = input("<:> ")

        if user_input in ("C", "c"):
            do_connect()

        if user_input in ("MC", "mc"):
            print("""
            ---------------------------------------------------
            Choose the index number to connect to that network.
            ---------------------------------------------------
            """)
            dict1 = {}
            ssids(dict1)
            if SSID_SUCCESS:
                us_in1 = input("<:> ")
                if us_in1 in dict1.keys():
                    wlan_connect(dict1[us_in1][0], dict1[us_in1][1])
                else:
                    print("Wrong input.")
                    time.sleep(2)
                    station()

        if user_input in ("A", "a"):
            do_append()
        if user_input in ("R", "r"):
            print("""
            ------------------------------------------------------------
            Choose the index number to add that network in the database.
            ------------------------------------------------------------
            """)
            dict2 = {}
            rdr(dict2, show=True)
            if RADAR_SUCCESS:
                us_in2 = input("<:> ")
                if us_in2 in dict2.keys():
                    do_append(dict2[us_in2])
                else:
                    print("Wrong input.")
                    time.sleep(2)
                    station()

        if user_input in ("D", "d"):
            print("""
            --------------------------------------------
            Choose the index number to remove a network.
            --------------------------------------------
            """)
            dict3 = {}
            ssids(dict3)
            if SSID_SUCCESS:
                us_in3 = input("<:> ")
                remove_data(us_in3, dict3.keys())

        if user_input in ("AP", "ap"):
            access_point()

        else:
            pass

    except SystemExit:
        print("SystemExit error.")


wlan.disconnect()
check()
