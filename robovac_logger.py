#!/usr/bin/env python3
"""Live logger for Eufy RoboVac status updates."""
from __future__ import annotations

import asyncio
import getpass
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Make the vendored robovac component importable when running the script from
# this repository without requiring installation as a package.
REPO_ROOT = Path(__file__).resolve().parent
ROBOVAC_VENDOR_PATH = REPO_ROOT / "vendor" / "robovac"
if ROBOVAC_VENDOR_PATH.exists():
    sys.path.insert(0, str(ROBOVAC_VENDOR_PATH))

# pylint: disable=wrong-import-position
from custom_components.robovac.const import PING_RATE, TIMEOUT  # type: ignore[attr-defined]
from custom_components.robovac.countries import (  # type: ignore[attr-defined]
    get_phone_code_by_country_code,
    get_phone_code_by_region,
    get_region_by_country_code,
    get_region_by_phone_code,
)
from custom_components.robovac.eufywebapi import EufyLogon  # type: ignore[attr-defined]
from custom_components.robovac.robovac import (  # type: ignore[attr-defined]
    ModelNotSupportedException,
    RoboVac,
)
from custom_components.robovac.tuyalocaldiscovery import (  # type: ignore[attr-defined]
    DiscoveryPortsNotAvailableException,
    TuyaLocalDiscovery,
)
from custom_components.robovac.tuyawebapi import TuyaAPISession  # type: ignore[attr-defined]

_LOGGER = logging.getLogger("robovac_logger")


class VacuumLoginError(RuntimeError):
    """Raised when the script cannot log in or locate a vacuum."""


def _fetch_first_vacuum_sync(email: str, password: str) -> Dict[str, Any]:
    """Blocking helper that authenticates with Eufy and Tuya."""
    eufy_session = EufyLogon(email, password)
    user_response = eufy_session.get_user_info()
    if user_response is None or user_response.status_code != 200:
        raise VacuumLoginError("Failed to reach the Eufy API. Check your credentials or network.")

    user_data = user_response.json()
    if user_data.get("res_code") != 1:
        raise VacuumLoginError("Authentication with the Eufy API was rejected.")

    user_info = user_data["user_info"]
    access_token = user_data["access_token"]

    device_response = eufy_session.get_device_info(
        user_info["request_host"], user_info["id"], access_token
    )
    if device_response is None:
        raise VacuumLoginError("Unable to retrieve the device list from Eufy.")
    device_data = device_response.json()

    settings_response = eufy_session.get_user_settings(
        user_info["request_host"], user_info["id"], access_token
    )
    if settings_response is None:
        raise VacuumLoginError("Unable to retrieve the user settings from Eufy.")
    settings_data = settings_response.json()

    region: str
    country_code: str

    tuya_home = settings_data.get("setting", {}).get("home_setting", {}).get("tuya_home", {})
    if "tuya_region_code" in tuya_home:
        region = tuya_home["tuya_region_code"] or "EU"
        if user_info.get("phone_code"):
            country_code = user_info["phone_code"]
        else:
            country_code = get_phone_code_by_region(region)
    elif user_info.get("phone_code"):
        region = get_region_by_phone_code(user_info["phone_code"])
        country_code = user_info["phone_code"]
    elif user_info.get("country"):
        region = get_region_by_country_code(user_info["country"])
        country_code = get_phone_code_by_country_code(user_info["country"])
    else:
        region = "EU"
        country_code = "44"

    timezone = user_info.get("timezone") or "UTC"
    tuya_client = TuyaAPISession(
        username="eh-" + user_info["id"],
        region=region,
        timezone=timezone,
        phone_code=country_code,
    )

    devices = device_data.get("devices", [])
    for item in devices:
        product = item.get("product", {})
        if product.get("appliance") != "Cleaning":
            continue

        try:
            tuya_device = tuya_client.get_device(item["id"])
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.debug("Skipping device %s due to Tuya API error: %s", item.get("id"), err)
            continue

        access_token = tuya_device.get("localKey")
        if not access_token:
            _LOGGER.debug("Device %s does not provide a local key", item.get("id"))
            continue

        return {
            "id": item["id"],
            "name": item.get("alias_name") or item.get("name") or "RoboVac",
            "model": product.get("product_code", ""),
            "description": item.get("name", "Eufy RoboVac"),
            "mac": item.get("wifi", {}).get("mac"),
            "access_token": access_token,
        }

    raise VacuumLoginError("No RoboVac devices were found on this Eufy account.")


async def fetch_first_vacuum(email: str, password: str) -> Dict[str, Any]:
    """Authenticate with the APIs using a background thread."""
    return await asyncio.to_thread(_fetch_first_vacuum_sync, email, password)


async def discover_device_ip(device_id: str, timeout: float = 60.0) -> str:
    """Listen for Tuya LAN broadcasts to determine the device's IP address."""
    loop = asyncio.get_running_loop()
    ip_future: asyncio.Future[str] = loop.create_future()

    async def handle_discovery(payload: Dict[str, Any]) -> None:
        if payload.get("gwId") != device_id:
            return
        ip_address = payload.get("ip")
        if ip_address and not ip_future.done():
            _LOGGER.info("Discovered %s at %s", device_id, ip_address)
            ip_future.set_result(ip_address)

    discovery = TuyaLocalDiscovery(handle_discovery)
    try:
        await discovery.start()
    except DiscoveryPortsNotAvailableException as err:
        discovery.close()
        raise VacuumLoginError(str(err)) from err

    try:
        return await asyncio.wait_for(ip_future, timeout=timeout)
    except asyncio.TimeoutError as err:
        raise VacuumLoginError(
            "Timed out waiting for the vacuum to announce itself on the local network."
        ) from err
    finally:
        discovery.close()


async def main() -> None:
    """Prompt for credentials, connect to the vacuum, and log updates."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s")

    email = input("Eufy email: ").strip()
    password = getpass.getpass("Eufy password: ")

    if not email or not password:
        raise SystemExit("Both email and password are required.")

    _LOGGER.info("Logging in to the Eufy and Tuya services...")
    vacuum_details = await fetch_first_vacuum(email, password)
    _LOGGER.info("Found RoboVac '%s' (model %s)", vacuum_details["name"], vacuum_details["model"])

    _LOGGER.info("Waiting for the vacuum to broadcast its IP address...")
    ip_address = await discover_device_ip(vacuum_details["id"])
    vacuum_details["ip_address"] = ip_address

    previous_state: Dict[str, Any] = {}

    async def log_state_update() -> None:
        nonlocal previous_state
        if vacuum is None:
            return
        current_state = vacuum.state
        if not current_state:
            return
        changes = {
            key: current_state[key]
            for key in current_state
            if previous_state.get(key) != current_state[key]
        }
        previous_state = dict(current_state)
        if not changes:
            return
        timestamp = datetime.now().isoformat(timespec="seconds")
        print(f"\n[{timestamp}] Received vacuum update:")
        print(json.dumps(changes, indent=2, sort_keys=True))
        print()

    model_code = (vacuum_details.get("model") or "")[:5]
    if not model_code:
        raise VacuumLoginError("The vacuum did not report a model code.")

    vacuum: Optional[RoboVac] = None
    try:
        vacuum = RoboVac(
            model_code=model_code,
            device_id=vacuum_details["id"],
            host=vacuum_details["ip_address"],
            local_key=vacuum_details["access_token"],
            timeout=TIMEOUT,
            ping_interval=PING_RATE,
            update_entity_state=log_state_update,
        )
    except ModelNotSupportedException as err:
        raise VacuumLoginError(f"Model {model_code} is not supported by the RoboVac integration.") from err

    try:
        await vacuum.async_connect()
        await vacuum.async_get()
        await log_state_update()
        print(
            "Listening for vacuum status changes... Go to your Eufy app and start a room "
            "clean to see the logs. Press Ctrl+C to exit."
        )
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nDisconnecting from the vacuum...")
    finally:
        await vacuum.async_disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except VacuumLoginError as err:
        _LOGGER.error("%s", err)
        raise SystemExit(1) from err
