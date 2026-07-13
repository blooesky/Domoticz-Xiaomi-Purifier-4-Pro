# Xiaomi Smart Air Purifier 4 Pro for Domoticz

Version 1.0.1

Local LAN plugin for **Xiaomi Smart Air Purifier 4 Pro**.

Tested device:

- Model: `zhimi.airp.vb4`
- Hardware: `esp32`
- Firmware tested: `2.2.10`
- Python: `3.11`
- `python-miio==0.5.12`
- `click==8.1.8`

The plugin uses an isolated Python virtual environment located inside the plugin directory. It does not alter the global `python-miio` installation and does not affect an existing Xiaomi Purifier Pro plugin.

## Features

- Power on/off
- Auto, Silent and Fan modes
- Fan level
- Favorite level
- PM2.5
- PM10
- Temperature
- Humidity
- Anion
- Buzzer
- Child lock
- LED brightness
- Filter life percentage
- Filter days remaining
- Filter hours used
- Motor speed
- Purified air volume
- Raw diagnostic status

## Installation

```bash
cd /home/pi/domoticz/plugins
mkdir -p XiaomiPurifier4Pro
cd XiaomiPurifier4Pro
```

Copy the files from this package into the directory, then run:

```bash
chmod +x install.sh update.sh uninstall.sh
./install.sh
sudo systemctl restart domoticz
```

Open Domoticz:

1. Go to **Setup → Hardware**.
2. Add **Xiaomi Smart Air Purifier 4 Pro**.
3. Enter the purifier IP address.
4. Enter its 32-character token.
5. Select a polling interval.
6. Press **Add**.

Reserve the purifier IP address in the router.

## Manual connectivity test

```bash
cd /home/pi/domoticz/plugins/XiaomiPurifier4Pro

.venv/bin/miiocli airpurifiermiot \
  --ip PURIFIER_IP \
  --token PURIFIER_TOKEN \
  --model zhimi.airp.vb4 \
  status
```

## Updating dependencies

```bash
cd /home/pi/domoticz/plugins/XiaomiPurifier4Pro
./update.sh
sudo systemctl restart domoticz
```

The dependency versions are deliberately pinned because `python-miio 0.5.12` is incompatible with newer Click releases.

## Troubleshooting

Check Domoticz logs:

```bash
sudo journalctl -u domoticz -n 200 --no-pager
```

Verify that the plugin imports the isolated library:

```bash
.venv/bin/python -c "import miio; print(miio.__file__)"
```

The returned path must point inside:

```text
/home/pi/domoticz/plugins/XiaomiPurifier4Pro/.venv/
```

If the plugin is not listed in Domoticz, confirm:

```bash
chmod 644 plugin.py
sudo systemctl restart domoticz
```

## Notes

- Communication is local over the LAN.
- The purifier must remain reachable from the Domoticz server.
- Commands are followed by a fresh status read, so Domoticz displays the actual device state.
- Values reported as unavailable by the purifier are ignored rather than written as invalid values.
