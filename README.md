# Pwnagotchi-ai32 plugins
Plugins from the [pwnagotchi-ai32 image](https://github.com/flippedgannet/pwnagotchi-ai32) (existing, not included in the image, and under development).
## bcap-update.py
Background bettercap OUI and caplets updater with pwnagotchi.cap protection, log cleaner, and recovery wipe in MANU mode. It isn't in the SB3 versions and won't be anymore; there isn't much point to it.
```toml
[main.plugins.bcap-update]
enabled = true #just one parameter – enable
```
Activates functions only after a 30-second wait following the start of MANU mode.

## bt-pan.py
An ultra-lightweight plugin for BT tethering that operates via the built-in bluetoothctl agent. It has no web interface or on-screen UI of its own, providing only parameters to output the UI through other plugins (such as control.py).
```toml
[main.plugins.bt-pan]
enabled = false
dhcp = true
interval = 60
```
There is a DHCP function for phones with dynamic IPs (like the Google Pixel 10 Pro), and it works perfectly for me.

## control.py
A plugin that displays the various current states of the device. Example configuration:
```toml
[main.plugins.control]
enabled = true
iface = true
iface_pos = "5,32"
blinds = true
blinds_pos = "50,32"
wan = true
wan_pos = "100,0"
ip = true
ip_pos = "0,96"
net_check_interval = 30
```
It is integrated with the bt-pan plugin; the status will show "WAN: BT," and the IP function will display the address for accessing the web interface via the host performing BT tethering, using port 8080.

## watchdog.py
This is by no means the original watchdog.py; it is a completely reworked plugin compared to the original. It features multiple stages, smart interface recovery without a reboot, and much more. Config (optional):
```toml
[main.plugins.watchdog]
enabled = true
max_blind_epochs = 15
```
Explanation of the `max_blind_epochs` parameter: this parameter specifies how many "blind" epochs the watchdog will tolerate before rebooting, without the interface dropping.

## hashielist.py
Ex18a's whitelist and hashvault plugins combined into one, with some improvements.
```toml
[main.plugins.hashielist]
enabled = true
whitelist = true
vault = true
```
1. VAULT (gated by `vault`, default off)
   Every *.pcap dropped into the handshake folder is run through
   hcxpcapngtool. A valid handshake lands as a *.22000 in the
   sibling `hashes` folder. pcaps that yield nothing are recorded
   in a hidden noshake cache so we never re-run the tool on them.

2. LIST (gated by `whitelist`, default on)
   Every *.22000 in `hashes` is parsed for the BSSID encoded in
   its filename. That MAC is appended to the whitelist file and
   pushed into the live runtime whitelist so pwnagotchi stops
   attacking an AP we already own.

## memtemp.py & gps.py
A slightly modified version of the Pwnagotchi `memtemp` plugin. It contains no hardcoded display settings, and all parameters can be easily rearranged or removed via the configuration file.
```toml
[main.plugins.memtemp]
enabled = false
scale = "celsius"
position = "x, y"
orientation = "horizontal"
fields = "mem, cpu, temp, freq"
```
As for hardcoding, the GPS plugin also received a few simple improvements, and the hardcoded display values ​​were removed:
```toml
[main.plugins.gps]
enabled = false
speed = 9600
device = "/dev/ttyACM0"
custom_pos = false
lat_pos = "132,85"
lon_pos = "128,95"
alt_pos = "132,105"
```
In any plugin, all position-related fields are optional; if they are not specified in the configuration, the plugin's default positions will be used. These defaults are set up for a display similar to the *Waveshare E-ink 2.13" v4*.
