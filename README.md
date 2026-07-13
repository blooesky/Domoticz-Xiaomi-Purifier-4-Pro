# Xiaomi Smart Air Purifier 4 Pro for Domoticz

Version 1.0.7

Local LAN plugin for controlling the **Xiaomi Smart Air Purifier 4 Pro** directly from Domoticz.

The plugin communicates locally with the purifier using its IP address and Xiaomi token. Xiaomi Cloud is not required during normal operation.

## Supported device

Tested with:

* Model: `zhimi.airp.vb4`
* Hardware: `esp32`
* Firmware: `2.2.10`
* Python: `3.11`
* `python-miio==0.5.12`
* `click==8.1.8`

The plugin uses an isolated Python virtual environment located inside its own directory.

It does not modify the global Python installation, does not replace the globally installed `python-miio` library and does not affect an existing Xiaomi Purifier Pro plugin.

## Features

* Power On / Off
* Auto mode
* Silent mode
* Fan mode
* Manual mode
* Fan Level 1–3
* Manual Level 1–14
* PM2.5
* PM10
* Temperature
* Humidity
* Anion control
* Buzzer control
* Child Lock
* LED brightness:

  * Off
  * Dim
  * Bright
* Filter life remaining
* Filter days remaining
* Filter hours used
* Motor speed
* Purified air volume
* Raw diagnostic status
* Configurable polling interval
* Optional diagnostic devices

## Operating modes

### Auto

The purifier automatically adjusts its operation according to the detected air quality.

### Silent

Low-noise operation intended for nighttime use.

### Fan

Fan mode uses the purifier's dedicated fan levels:

* Level 1
* Level 2
* Level 3

These are not the same as the Manual mode levels.

Fan Level 1 is stronger than normal Auto operation, Fan Level 2 is stronger and Fan Level 3 runs approximately at maximum fan speed.

### Manual

Manual mode uses Xiaomi Favorite Level values:

* Level 1 to Level 14

The selected Manual Level controls the airflow intensity while Manual mode is active.

## Devices created in Domoticz

The plugin creates the following devices:

```text
Purifier Power
Operation Mode
Fan Level
Manual Level
PM2.5
PM10
Temperature
Humidity
Anion
Buzzer
Child Lock
LED Brightness
Filter Life
Filter Days Remaining
Filter Hours Used
Motor Speed
Purify Volume
Raw Status
```

Diagnostic devices can be disabled from the hardware configuration.

## Requirements

* Domoticz with Python Plugin System enabled
* Python 3.11 or compatible
* Python virtual environment support
* Xiaomi purifier IP address
* Xiaomi device token
* Purifier and Domoticz server connected to the same local network

On Debian or Raspberry Pi OS, install Python virtual environment support if necessary:

```bash
sudo apt update
sudo apt install python3-venv
```

It is recommended to reserve the purifier IP address in the router.

## Installation

Open a terminal on the Domoticz server:

```bash
cd /home/pi/domoticz/plugins
```

Clone the repository:

```bash
git clone https://github.com/blooesky/Domoticz-Xiaomi-Purifier-4-Pro.git XiaomiPurifier4Pro
```

Open the plugin directory:

```bash
cd XiaomiPurifier4Pro
```

Make the scripts executable:

```bash
chmod +x install.sh update.sh uninstall.sh
```

Run the installer:

```bash
./install.sh
```

Restart Domoticz:

```bash
sudo systemctl restart domoticz
```

## Domoticz configuration

After restarting Domoticz:

1. Open **Setup → Hardware**.
2. Add a new hardware device.
3. Select **Xiaomi Smart Air Purifier 4 Pro**.
4. Enter the purifier IP address.
5. Enter its 32-character Xiaomi token.
6. Select the polling interval.
7. Choose whether diagnostic devices should be created.
8. Press **Add**.

## Python virtual environment

All Python dependencies are installed inside:

```text
/home/pi/domoticz/plugins/XiaomiPurifier4Pro/.venv
```

Pinned dependencies:

```text
python-miio==0.5.12
click==8.1.8
```

The Click version is deliberately pinned because newer Click releases are incompatible with the command-line interface included in `python-miio 0.5.12`.

## Manual connectivity test

Open the plugin directory:

```bash
cd /home/pi/domoticz/plugins/XiaomiPurifier4Pro
```

Check device information:

```bash
.venv/bin/miiocli device \
  --ip PURIFIER_IP \
  --token PURIFIER_TOKEN \
  info
```

Expected model:

```text
zhimi.airp.vb4
```

Check purifier status:

```bash
.venv/bin/miiocli airpurifiermiot \
  --ip PURIFIER_IP \
  --token PURIFIER_TOKEN \
  --model zhimi.airp.vb4 \
  status
```

## Updating the plugin

Open the plugin directory:

```bash
cd /home/pi/domoticz/plugins/XiaomiPurifier4Pro
```

Download the latest files:

```bash
git pull
```

Update the isolated dependencies:

```bash
./update.sh
```

Restart Domoticz:

```bash
sudo systemctl restart domoticz
```

A complete update can be performed with:

```bash
cd /home/pi/domoticz/plugins/XiaomiPurifier4Pro
git pull
./update.sh
sudo systemctl restart domoticz
```

## Uninstalling

First remove the hardware entry from Domoticz.

To remove only the isolated Python virtual environment:

```bash
cd /home/pi/domoticz/plugins/XiaomiPurifier4Pro
./uninstall.sh
```

To completely remove the plugin:

```bash
sudo systemctl stop domoticz
rm -rf /home/pi/domoticz/plugins/XiaomiPurifier4Pro
sudo systemctl start domoticz
```

## Troubleshooting

### Plugin does not appear in Domoticz

Check file permissions:

```bash
cd /home/pi/domoticz/plugins/XiaomiPurifier4Pro
chmod 644 plugin.py
chmod +x install.sh update.sh uninstall.sh
sudo systemctl restart domoticz
```

### Check Domoticz logs

Show the latest log entries:

```bash
sudo journalctl -u domoticz -n 200 --no-pager
```

Follow the live log:

```bash
sudo journalctl -u domoticz -f
```

### Verify the isolated library

```bash
cd /home/pi/domoticz/plugins/XiaomiPurifier4Pro

.venv/bin/python -c "import miio; print(miio.__file__)"
```

The returned path must point inside:

```text
/home/pi/domoticz/plugins/XiaomiPurifier4Pro/.venv/
```

It must not point to:

```text
/usr/local/lib/python3.11/
```

### Token error

The Xiaomi token must contain exactly 32 hexadecimal characters.

Example format:

```text
0123456789abcdef0123456789abcdef
```

Never publish your real token.

### Device does not respond

Check that:

* the purifier IP address is correct;
* the token belongs to the same purifier;
* the purifier and Domoticz server are on the same local network;
* Wi-Fi client isolation is disabled;
* UDP communication is not blocked;
* the purifier IP address has not changed.

### LED Bright mode

The plugin contains a dedicated correction for LED Bright mode on `zhimi.airp.vb4`.

In `python-miio 0.5.12`, the Bright value is not mapped correctly for this model. The plugin sends the correct MIoT value while preserving the normal Off and Dim behavior.

## Notes

* Communication is performed locally over the LAN.
* Xiaomi Cloud is not required during normal plugin operation.
* Commands are followed by a fresh status read, so Domoticz displays the actual purifier state.
* Values reported as unavailable by the purifier are ignored instead of being written as invalid sensor values.
* Fan Level 1–3 and Manual Level 1–14 are separate controls.
* The purifier should have a reserved IP address in the router.

## Security

Do not publish:

* your Xiaomi device token;
* private IP configuration;
* Domoticz credentials;
* screenshots containing authentication information.

Never place a real token directly inside `plugin.py`, `README.md`, GitHub issues or commits.

## Credits

This plugin uses:

* `python-miio`
* Domoticz Python Plugin System

`python-miio` is developed and maintained by its respective contributors and is distributed under its own license.

## License

See the `LICENSE` file included in this repository.
