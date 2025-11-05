"""Minimal subset of Home Assistant constants used by the RoboVac logger."""
from __future__ import annotations
from enum import Enum

EVENT_HOMEASSISTANT_STOP = "homeassistant_stop"
CONF_IP_ADDRESS = "ip_address"
CONF_ACCESS_TOKEN = "access_token"
CONF_DESCRIPTION = "description"
CONF_ID = "id"
CONF_MAC = "mac"
CONF_MODEL = "model"
CONF_NAME = "name"


class Platform(str, Enum):
    """Small subset of platform identifiers from Home Assistant."""

    VACUUM = "vacuum"
    SENSOR = "sensor"
