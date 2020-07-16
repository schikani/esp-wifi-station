# esp-wifi-station in MicroPython

It is a lightweight Wifi station for ESP8266/32 in Micropython. It is capable of auto-connecting to the available networks when the device is powered on. You can also set an access name and password in ESP8266 (in ESP32 access name and max_clients) to let other devices connect to your station. 
A second file is a json file with network credentials which is created automatically and it is the main database.

## Uploading the esp_station file.

### Method 1 (High RAM)
This method is for the models with higher RAM. It uses a normal python script without pre-compiling (.py file) which is later compiled and uses more system resources.

Upload "esp_wifi_station.py" with "boot.py" adding the following line in "boot.py"
> from esp_wifi_station import *

If it doesn't work or you get a memory allocation error, follow Method 2.


### Method 2 (Low RAM)
This method is for the models with lower RAM. It uses the pre-compiled python script (.mpy file) to use small RAM efficiently.

Upload "esp_wifi_station.mpy" with "boot.py" adding the following line in "boot.py"
> from esp_wifi_station import *

## Getting the following text.
You will get the below text because, there is no database (.json file) in your system so, a new json file is created automatically with default settings and values at the next reboot.

				----------------------------------------------------
					  Curently there is no database
				A new database will be created with a system reboot.
				----------------------------------------------------

After the auto-reboot, the script reads the values from the newly created json file (which will be our database).

			<>_<> Board type: esp8266
			<>_<> Discoverable as: ESP_Station
			<>_<> Network config: ('192.168.4.1', '255.255.255.0', '192.168.4.1', '0.0.0.0')

			Attempting auto-connection...


			    There is no database with saved networks.
			    Returning to the station.
                
You can change the AP settings, Add/Remove networks, Auto-connect/Manually-connect to networks from the station console.

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


## Saving a network.

### Method 1
Add a network by "R" command which starts the Radar and shows the available networks. You can add a network simply by typing the index of the network.

### Method 2
Add a network by "A" command which adds ssid after you type the ssid manually.


If the network is in the database and if it is in the range of device, it will automatically connect.
Now with the next reboot, after 5 seconds, the station will attempt auto-connect and you will get the following text.


				Attempting auto-connection...
				found: (the available network)
				connecting...

				<>_<> connected to: (Your SSID will be displayed)
				<>_<> network config: (Your IP and other info will be displayed)


If the station can't find any available networks it will show the following text and you will be sent back to the station.


			    Sorry, no network on radar matches the saved networks.
			    Returning to the station.	
			    
## Call the station console by calling "station()" from the MicroPython REPL
