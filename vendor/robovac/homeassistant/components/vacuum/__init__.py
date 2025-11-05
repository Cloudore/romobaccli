"""Minimal stubs of Home Assistant vacuum enums for standalone scripts."""
from __future__ import annotations

from enum import Enum, IntFlag


class VacuumActivity(str, Enum):
    """Subset of Home Assistant's VacuumActivity enum."""

    CLEANING = "cleaning"
    DOCKED = "docked"
    ERROR = "error"
    IDLE = "idle"
    PAUSED = "paused"
    RETURNING = "returning"


class VacuumEntityFeature(IntFlag):
    """Subset of Home Assistant's VacuumEntityFeature flags used by the vendor code."""

    NONE = 0
    TURN_ON = 1 << 0
    TURN_OFF = 1 << 1
    START = 1 << 2
    STOP = 1 << 3
    RETURN_HOME = 1 << 4
    FAN_SPEED = 1 << 5
    BATTERY = 1 << 6
    STATE = 1 << 7
    STATUS = STATE
    LOCATE = 1 << 8
    CLEAN_SPOT = 1 << 9
    PAUSE = 1 << 10
    SEND_COMMAND = 1 << 11
    MAP = 1 << 12


__all__ = [
    "VacuumActivity",
    "VacuumEntityFeature",
]
