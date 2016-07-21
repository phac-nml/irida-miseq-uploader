import os
import logging

from ConfigParser import RawConfigParser, NoOptionError
from appdirs import user_config_dir
from collections import namedtuple

user_config_file = os.path.join(user_config_dir("iridaUploader"), "config.conf")
conf_parser = RawConfigParser()

SettingsDefault = namedtuple('SettingsDefault', ['setting', 'default_value'])

default_settings = [SettingsDefault._make(["client_id", ""]),
                    SettingsDefault._make(["client_secret", ""]),
                    SettingsDefault._make(["username", ""]),
                    SettingsDefault._make(["password", ""]),
                    SettingsDefault._make(["baseurl", ""]),
                    SettingsDefault._make(["completion_cmd", ""]),
                    SettingsDefault._make(["default_dir", os.path.expanduser("~")]),
                    SettingsDefault._make(["monitor_default_dir", "False"])]

if os.path.exists(user_config_file):
    logging.info("Loading configuration settings from {}".format(user_config_file))

    conf_parser.read(user_config_file)

    for config in default_settings:
        if not conf_parser.has_option("Settings", config.setting):
            conf_parser.set("Settings", config.setting, config.default_value)
else:
    logging.info("No default config file exists, loading defaults.")
    conf_parser.add_section("Settings")
    for config in default_settings:
            conf_parser.set("Settings", config.setting, config.default_value)

def read_config_option(key, expected_type=None, default_value=None):
    """Read the specified value from the configuration file.

    Args:
        key: the name of the key to read from the config file.
        expected_type: read the config option as the specified type (if specified)
        default_value: if the key doesn't exist, just return the default value.
            If the default value is not specified, the function will throw whatever
            error was raised by the configuration parser
    """
    logging.info("Reading config option {} with expected type {}".format(key, expected_type))

    try:
        if not expected_type:
            value = conf_parser.get("Settings", key)
            logging.info("Got configuration for key {}: {}".format(key, value))
            return conf_parser.get("Settings", key)
        elif expected_type is bool:
            return conf_parser.getboolean("Settings", key)
    except (ValueError, NoOptionError) as e:
        if default_value:
            return default_value
        else:
            raise

def write_config_option(field_name, field_value):
    """Write the configuration file out with the new key.

    Args:
        field_name: the name of the field to write
        field_value: the value to write to the file
    """
    conf_parser.set("Settings", field_name, field_value)

    if not os.path.exists(os.path.dirname(user_config_file)):
        os.makedirs(os.path.dirname(user_config_file))

    with open(user_config_file, 'wb') as config_file:
        conf_parser.write(config_file)
