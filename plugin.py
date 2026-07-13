# Xiaomi Smart Air Purifier 4 Pro plugin for Domoticz
# Model tested: zhimi.airp.vb4
# Local communication through python-miio (isolated .venv)

"""
<plugin key="XiaomiPurifier4Pro" name="Xiaomi Smart Air Purifier 4 Pro" author="4D" version="1.0.7" wikilink="https://github.com/blooesky/Domoticz-Xiaomi-Purifier-4-Pro"
        externallink="https://github.com/blooesky/Domoticz-Xiaomi-Purifier-4-Pro">
    <description>
        <h2>Xiaomi Smart Air Purifier 4 Pro</h2>
        <p>Local LAN control for model zhimi.airp.vb4 using IP and token.</p>
        <p>The plugin loads python-miio exclusively from the .venv inside its own directory.</p>
    </description>
    <params>
        <param field="Address" label="Purifier IP address" width="200px" required="true" default="192.168.0.100"/>
        <param field="Mode1" label="Token (32 hexadecimal characters)" width="320px" required="true"/>
        <param field="Mode2" label="Polling interval" width="100px">
            <options>
                <option label="15 seconds" value="15"/>
                <option label="30 seconds" value="30" default="true"/>
                <option label="60 seconds" value="60"/>
                <option label="120 seconds" value="120"/>
                <option label="300 seconds" value="300"/>
            </options>
        </param>
        <param field="Mode3" label="Create diagnostic devices" width="100px">
            <options>
                <option label="Yes" value="Yes" default="true"/>
                <option label="No" value="No"/>
            </options>
        </param>
        <param field="Mode6" label="Debug" width="100px">
            <options>
                <option label="No" value="Normal" default="true"/>
                <option label="Yes" value="Debug"/>
            </options>
        </param>
    </params>
</plugin>
"""

import os
import sys
import json
import time
import traceback
from enum import Enum

import Domoticz

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))


def _add_venv_to_path():
    """Load only the virtual environment located inside this plugin."""
    candidates = [
        os.path.join(PLUGIN_DIR, ".venv", "lib", "python3.11", "site-packages"),
        os.path.join(PLUGIN_DIR, ".venv", "lib", "python3.12", "site-packages"),
        os.path.join(PLUGIN_DIR, ".venv", "lib", "python3.10", "site-packages"),
    ]
    for path in candidates:
        if os.path.isdir(path) and path not in sys.path:
            sys.path.insert(0, path)
            return path
    raise RuntimeError(
        "Virtual environment not found. Run ./install.sh inside the plugin directory."
    )


VENV_SITE_PACKAGES = _add_venv_to_path()

try:
    # python-miio 0.5.12 package layout
    from miio.integrations.airpurifier.zhimi.airpurifier_miot import (
        AirPurifierMiot,
        OperationMode,
        LedBrightness,
    )
except ImportError:
    # Compatibility fallback for alternative python-miio package layouts.
    from miio import AirPurifierMiot
    try:
        from miio.integrations.airpurifier.zhimi.airpurifier_miot import (
            OperationMode,
            LedBrightness,
        )
    except ImportError:
        from miio.airpurifier_miot import OperationMode, LedBrightness


UNIT_POWER = 1
UNIT_MODE = 2
UNIT_FAN_LEVEL = 3
UNIT_FAVORITE_LEVEL = 4
UNIT_PM25 = 5
UNIT_PM10 = 6
UNIT_TEMPERATURE = 7
UNIT_HUMIDITY = 8
UNIT_ANION = 9
UNIT_BUZZER = 10
UNIT_CHILD_LOCK = 11
UNIT_LED_BRIGHTNESS = 12
UNIT_FILTER_LIFE = 13
UNIT_FILTER_DAYS = 14
UNIT_FILTER_HOURS = 15
UNIT_MOTOR_SPEED = 16
UNIT_PURIFY_VOLUME = 17
UNIT_RAW_STATUS = 18

MODE_LEVELS = {
    0: "Off",
    10: "Auto",
    20: "Silent",
    30: "Fan",
    40: "Manual",
}

LED_LEVELS = {
    0: "Off",
    10: "Dim",
    20: "Bright",
}


class BasePlugin:
    def __init__(self):
        self.device = None
        self.ip = ""
        self.token = ""
        self.poll_interval = 30
        self.heartbeat_seconds = 10
        self.heartbeat_counter = 0
        self.command_in_progress = False
        self.last_success = 0
        self.error_count = 0

    def onStart(self):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
            Domoticz.Debug("Debug logging enabled.")

        self.ip = Parameters["Address"].strip()
        self.token = Parameters["Mode1"].strip()

        try:
            self.poll_interval = max(10, int(Parameters["Mode2"]))
        except Exception:
            self.poll_interval = 30

        if not self.ip:
            Domoticz.Error("Purifier IP address is missing.")
            return

        if len(self.token) != 32:
            Domoticz.Error("The token must contain exactly 32 hexadecimal characters.")
            return

        try:
            int(self.token, 16)
        except ValueError:
            Domoticz.Error("The token contains non-hexadecimal characters.")
            return

        self._create_devices()

        try:
            self.device = AirPurifierMiot(
                self.ip,
                self.token,
                model="zhimi.airp.vb4",
            )
        except TypeError:
            # Compatibility fallback for older constructor signatures.
            self.device = AirPurifierMiot(self.ip, self.token)

        Domoticz.Heartbeat(self.heartbeat_seconds)
        Domoticz.Log(
            "Xiaomi Purifier 4 Pro started. IP: {}, polling: {} seconds, library: {}".format(
                self.ip, self.poll_interval, VENV_SITE_PACKAGES
            )
        )
        self._refresh_status(force=True)

    def onStop(self):
        Domoticz.Log("Xiaomi Purifier 4 Pro plugin stopped.")

    def onConnect(self, Connection, Status, Description):
        pass

    def onMessage(self, Connection, Data):
        pass

    def onDisconnect(self, Connection):
        pass

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        pass

    def onCommand(self, Unit, Command, Level, Color):
        if self.device is None:
            Domoticz.Error("The purifier client is not initialized.")
            return

        Domoticz.Debug(
            "Command received: Unit={}, Command={}, Level={}".format(Unit, Command, Level)
        )

        self.command_in_progress = True
        try:
            if Unit == UNIT_POWER:
                self.device.on() if Command == "On" else self.device.off()

            elif Unit == UNIT_MODE:
                self._set_mode(int(Level))

            elif Unit == UNIT_FAN_LEVEL:
                self.device.set_fan_level(self._selector_to_value(Level, 1, 3))

            elif Unit == UNIT_FAVORITE_LEVEL:
                self.device.set_favorite_level(self._selector_to_value(Level, 1, 14))

            elif Unit == UNIT_ANION:
                self.device.set_anion(Command == "On")

            elif Unit == UNIT_BUZZER:
                self.device.set_buzzer(Command == "On")

            elif Unit == UNIT_CHILD_LOCK:
                self.device.set_child_lock(Command == "On")

            elif Unit == UNIT_LED_BRIGHTNESS:
                self._set_led_brightness(int(Level))

            else:
                Domoticz.Error("Unsupported command for unit {}.".format(Unit))
                return

            time.sleep(0.7)
            self._refresh_status(force=True)

        except Exception as error:
            self._log_exception("Command failed", error)
            # Restore the real state after a failed command.
            self._refresh_status(force=True)
        finally:
            self.command_in_progress = False

    def onHeartbeat(self):
        if self.command_in_progress:
            return

        self.heartbeat_counter += self.heartbeat_seconds
        if self.heartbeat_counter >= self.poll_interval:
            self.heartbeat_counter = 0
            self._refresh_status()

    def _create_devices(self):
        self._create_switch(UNIT_POWER, "Purifier Power")
        self._create_selector(
            UNIT_MODE,
            "Operation Mode",
            "Off|Auto|Silent|Fan|Manual",
        )
        self._create_selector(
            UNIT_FAN_LEVEL,
            "Fan Level",
            "Off|1|2|3",
        )
        self._create_selector(
            UNIT_FAVORITE_LEVEL,
            "Favorite Level",
            "Off|1|2|3|4|5|6|7|8|9|10|11|12|13|14",
        )

        if UNIT_PM25 not in Devices:
            Domoticz.Device(
                Name="PM2.5",
                Unit=UNIT_PM25,
                Type=243,
                Subtype=31,
                Options={"Custom": "1;µg/m³"},
                Used=1,
            ).Create()

        if UNIT_PM10 not in Devices:
            Domoticz.Device(
                Name="PM10",
                Unit=UNIT_PM10,
                Type=243,
                Subtype=31,
                Options={"Custom": "1;µg/m³"},
                Used=1,
            ).Create()

        if UNIT_TEMPERATURE not in Devices:
            Domoticz.Device(
                Name="Temperature",
                Unit=UNIT_TEMPERATURE,
                Type=80,
                Subtype=5,
                Used=1,
            ).Create()

        if UNIT_HUMIDITY not in Devices:
            Domoticz.Device(
                Name="Humidity",
                Unit=UNIT_HUMIDITY,
                Type=81,
                Subtype=1,
                Used=1,
            ).Create()

        self._create_switch(UNIT_ANION, "Anion")
        self._create_switch(UNIT_BUZZER, "Buzzer")
        self._create_switch(UNIT_CHILD_LOCK, "Child Lock")
        self._create_selector(
            UNIT_LED_BRIGHTNESS,
            "LED Brightness",
            "Off|Dim|Bright",
        )

        if UNIT_FILTER_LIFE not in Devices:
            Domoticz.Device(
                Name="Filter Life",
                Unit=UNIT_FILTER_LIFE,
                Type=243,
                Subtype=6,
                Used=1,
            ).Create()

        if UNIT_FILTER_DAYS not in Devices:
            Domoticz.Device(
                Name="Filter Days Remaining",
                Unit=UNIT_FILTER_DAYS,
                Type=243,
                Subtype=31,
                Options={"Custom": "1;days"},
                Used=1,
            ).Create()

        if Parameters["Mode3"] == "Yes":
            self._create_custom(UNIT_FILTER_HOURS, "Filter Hours Used", "hours")
            self._create_custom(UNIT_MOTOR_SPEED, "Motor Speed", "rpm")
            self._create_custom(UNIT_PURIFY_VOLUME, "Purify Volume", "m³")

            if UNIT_RAW_STATUS not in Devices:
                Domoticz.Device(
                    Name="Raw Status",
                    Unit=UNIT_RAW_STATUS,
                    Type=243,
                    Subtype=19,
                    Used=1,
                ).Create()

    @staticmethod
    def _create_switch(unit, name):
        if unit not in Devices:
            Domoticz.Device(
                Name=name,
                Unit=unit,
                Type=244,
                Subtype=73,
                Switchtype=0,
                Used=1,
            ).Create()

    @staticmethod
    def _create_selector(unit, name, level_names):
        if unit not in Devices:
            Domoticz.Device(
                Name=name,
                Unit=unit,
                Type=244,
                Subtype=62,
                Switchtype=18,
                Options={
                    "LevelActions": "||||||||||||||||",
                    "LevelNames": level_names,
                    "LevelOffHidden": "false",
                    "SelectorStyle": "0",
                },
                Used=1,
            ).Create()

    @staticmethod
    def _create_custom(unit, name, suffix):
        if unit not in Devices:
            Domoticz.Device(
                Name=name,
                Unit=unit,
                Type=243,
                Subtype=31,
                Options={"Custom": "1;{}".format(suffix)},
                Used=1,
            ).Create()

    def _refresh_status(self, force=False):
        if self.device is None:
            return

        try:
            status = self.device.status()
            self.error_count = 0
            self.last_success = int(time.time())

            power = self._value(status, "power")
            mode = self._value(status, "mode")
            fan_level = self._value(status, "fan_level")
            favorite_level = self._value(status, "favorite_level")
            aqi = self._value(status, "aqi")
            pm10 = self._value(status, "pm10_density")
            temperature = self._value(status, "temperature")
            humidity = self._value(status, "humidity")
            anion = self._value(status, "anion")
            buzzer = self._value(status, "buzzer")
            child_lock = self._value(status, "child_lock")
            led_brightness = self._value(status, "led_brightness")
            filter_life = self._value(status, "filter_life_remaining")
            filter_days = self._value(status, "filter_left_time")
            filter_hours = self._value(status, "filter_hours_used")
            motor_speed = self._value(status, "motor_speed")
            purify_volume = self._value(status, "purify_volume")

            self._update_switch(UNIT_POWER, power, force)
            self._update_selector(UNIT_MODE, self._mode_to_level(mode), force)

            if fan_level is not None:
                self._update_selector(
                    UNIT_FAN_LEVEL,
                    max(0, min(3, int(fan_level))) * 10,
                    force,
                )

            if favorite_level is not None:
                self._update_selector(
                    UNIT_FAVORITE_LEVEL,
                    max(0, min(14, int(favorite_level))) * 10,
                    force,
                )

            self._update_number(UNIT_PM25, aqi, force)
            self._update_number(UNIT_PM10, pm10, force)
            self._update_number(UNIT_TEMPERATURE, temperature, force)
            self._update_humidity(UNIT_HUMIDITY, humidity, force)

            self._update_switch(UNIT_ANION, anion, force)
            self._update_switch(UNIT_BUZZER, buzzer, force)
            self._update_switch(UNIT_CHILD_LOCK, child_lock, force)
            self._update_selector(
                UNIT_LED_BRIGHTNESS,
                self._led_to_level(led_brightness),
                force,
            )

            self._update_number(UNIT_FILTER_LIFE, filter_life, force, integer=True)
            self._update_number(UNIT_FILTER_DAYS, filter_days, force, integer=True)

            if Parameters["Mode3"] == "Yes":
                self._update_number(UNIT_FILTER_HOURS, filter_hours, force, integer=True)
                self._update_number(UNIT_MOTOR_SPEED, motor_speed, force, integer=True)
                self._update_number(UNIT_PURIFY_VOLUME, purify_volume, force, integer=True)
                self._update_raw_status(status, force)

            Domoticz.Debug("Purifier status refreshed successfully.")

        except Exception as error:
            self.error_count += 1
            self._log_exception(
                "Unable to read purifier status (failure #{})".format(self.error_count),
                error,
            )

    @staticmethod
    def _value(status, name):
        """Read a status property regardless of whether it is a property or method."""
        try:
            value = getattr(status, name)
        except AttributeError:
            return None

        try:
            if callable(value):
                value = value()
        except Exception:
            return None

        if isinstance(value, Enum):
            return value
        return value

    @staticmethod
    def _enum_name(value):
        if value is None:
            return ""
        if isinstance(value, Enum):
            return value.name.lower()
        text = str(value).lower()
        if "." in text:
            text = text.rsplit(".", 1)[-1]
        return text

    def _set_mode(self, level):
        mode_name = {
            10: "Auto",
            20: "Silent",
            30: "Fan",
            # Xiaomi exposes Manual mode as Favorite.
            40: "Favorite",
        }.get(level)

        if not mode_name:
            self.device.off()
            return

        enum_value = self._find_enum(OperationMode, mode_name)
        self.device.set_mode(enum_value)

    def _set_led_brightness(self, level):
        name = {
            0: "Off",
            10: "Dim",
            20: "Bright",
        }.get(level, "Bright")

        # python-miio 0.5.12 contains a conversion bug for Bright on
        # zhimi.airp.vb4: LedBrightness.Bright has value 0 and is not
        # reversed to the device value 2. Send the correct MIoT value
        # directly only for Bright. Off and Dim continue through the
        # standard library method.
        if name == "Bright":
            self.device.set_property("led_brightness", 2)
            return

        enum_value = self._find_enum(LedBrightness, name)
        self.device.set_led_brightness(enum_value)

    @staticmethod
    def _find_enum(enum_class, desired_name):
        desired = desired_name.lower()
        aliases = {
            "dim": ("dim", "low"),
            "bright": ("bright", "high"),
            "off": ("off",),
            "auto": ("auto",),
            "silent": ("silent",),
            "fan": ("fan",),
            "favorite": ("favorite", "manual"),
        }

        wanted = aliases.get(desired, (desired,))
        for member in enum_class:
            member_name = member.name.lower()
            member_value = str(member.value).lower()
            if member_name in wanted or member_value in wanted:
                return member

        raise ValueError(
            "No compatible {} value found for '{}'.".format(
                enum_class.__name__, desired_name
            )
        )

    def _mode_to_level(self, mode):
        name = self._enum_name(mode)
        if "auto" in name:
            return 10
        if "silent" in name:
            return 20
        if "fan" in name:
            return 30
        if "favorite" in name or "manual" in name:
            return 40
        return 0

    def _led_to_level(self, brightness):
        name = self._enum_name(brightness)
        if "off" in name:
            return 0
        if "dim" in name or "low" in name:
            return 10
        if "bright" in name or "high" in name:
            return 20
        return 20

    @staticmethod
    def _selector_to_value(level, minimum, maximum):
        value = int(round(float(level) / 10.0))
        return max(minimum, min(maximum, value))

    @staticmethod
    def _update_switch(unit, value, force=False):
        if unit not in Devices or value is None:
            return

        if isinstance(value, str):
            normalized = value.strip().lower()
            is_on = normalized in ("on", "true", "1", "yes", "enabled")
        else:
            is_on = bool(value)

        nvalue = 1 if is_on else 0
        svalue = "On" if is_on else "Off"
        if force or Devices[unit].nValue != nvalue or Devices[unit].sValue != svalue:
            Devices[unit].Update(nValue=nvalue, sValue=svalue)

    @staticmethod
    def _update_selector(unit, level, force=False):
        if unit not in Devices or level is None:
            return
        level = int(level)
        svalue = str(level)
        nvalue = 0 if level == 0 else 1
        if force or Devices[unit].nValue != nvalue or Devices[unit].sValue != svalue:
            Devices[unit].Update(nValue=nvalue, sValue=svalue)

    @staticmethod
    def _update_number(unit, value, force=False, integer=False):
        if unit not in Devices or value is None:
            return
        try:
            if integer:
                svalue = str(int(round(float(value))))
            else:
                numeric = float(value)
                svalue = str(int(numeric)) if numeric.is_integer() else str(round(numeric, 2))
        except (TypeError, ValueError):
            return

        if force or Devices[unit].sValue != svalue:
            Devices[unit].Update(nValue=0, sValue=svalue)


    @staticmethod
    def _update_humidity(unit, value, force=False):
        if unit not in Devices or value is None:
            return

        try:
            humidity = max(0, min(100, int(round(float(value)))))
        except (TypeError, ValueError):
            return

        # Domoticz humidity sensor expects the percentage in nValue.
        # sValue is the humidity status: 0=Normal, 1=Comfortable,
        # 2=Dry, 3=Wet.
        if humidity < 30:
            humidity_status = "2"
        elif humidity > 70:
            humidity_status = "3"
        elif 40 <= humidity <= 60:
            humidity_status = "1"
        else:
            humidity_status = "0"

        if (
            force
            or Devices[unit].nValue != humidity
            or Devices[unit].sValue != humidity_status
        ):
            Devices[unit].Update(nValue=humidity, sValue=humidity_status)

    def _update_raw_status(self, status, force=False):
        if UNIT_RAW_STATUS not in Devices:
            return

        raw = {}
        fields = (
            "power", "anion", "aqi", "average_aqi", "humidity", "temperature",
            "pm10_density", "fan_level", "mode", "led", "led_brightness",
            "buzzer", "child_lock", "favorite_level", "filter_life_remaining",
            "filter_hours_used", "filter_left_time", "purify_volume",
            "motor_speed", "filter_rfid_product_id", "filter_rfid_tag",
            "filter_type",
        )

        for field in fields:
            value = self._value(status, field)
            if isinstance(value, Enum):
                value = value.name
            if value is not None:
                raw[field] = value

        text = json.dumps(raw, ensure_ascii=False, separators=(",", ":"))
        if force or Devices[UNIT_RAW_STATUS].sValue != text:
            Devices[UNIT_RAW_STATUS].Update(nValue=0, sValue=text)

    @staticmethod
    def _log_exception(prefix, error):
        Domoticz.Error("{}: {}".format(prefix, error))
        Domoticz.Debug(traceback.format_exc())


_global_plugin = BasePlugin()


def onStart():
    _global_plugin.onStart()


def onStop():
    _global_plugin.onStop()


def onConnect(Connection, Status, Description):
    _global_plugin.onConnect(Connection, Status, Description)


def onMessage(Connection, Data):
    _global_plugin.onMessage(Connection, Data)


def onCommand(Unit, Command, Level, Color):
    _global_plugin.onCommand(Unit, Command, Level, Color)


def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    _global_plugin.onNotification(
        Name, Subject, Text, Status, Priority, Sound, ImageFile
    )


def onDisconnect(Connection):
    _global_plugin.onDisconnect(Connection)


def onHeartbeat():
    _global_plugin.onHeartbeat()
