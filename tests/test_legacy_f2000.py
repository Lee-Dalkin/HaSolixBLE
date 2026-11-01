# ruff: noqa: CPY001
"""Regression checks for the original 767/F2000 (A1780) legacy model.

These tests exercise Home Assistant sensor registration without BLE hardware.
They require a SolixBLE build exporting F2000Legacy.
"""

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import patch

import pytest
from homeassistant.components.sensor.const import SensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from SolixBLE import ChargingStatus, F2000Legacy  # type: ignore[import-untyped]

from custom_components.solix_ble import SolixBLEConfigEntry, get_power_station_class
from custom_components.solix_ble.const import CHARGING_STATUS_C300_STRINGS, Models
from custom_components.solix_ble.sensor import (
    SolixSensorEntity,
    async_setup_entry,
)


@pytest.mark.asyncio
async def test_legacy_f2000_sensor_attribute_and_charging_labels() -> None:
    """Register legacy 767 sensors using attributes and enum labels it supports."""
    assert get_power_station_class(Models.F2000_OLD) is F2000Legacy
    assert hasattr(F2000Legacy, "ac_charging_power")

    # We test which entities are registered, not a live Bluetooth connection.
    # Entity construction is mocked so telemetry and BLE state are unnecessary.
    device = object.__new__(F2000Legacy)
    entities: list[tuple[Any, ...]] = []

    with patch(
        "custom_components.solix_ble.sensor.SolixSensorEntity",
        side_effect=lambda *args, **_kwargs: args,
    ):
        await async_setup_entry(
            cast("HomeAssistant", None),  # hass is not used by this sensor factory
            cast("SolixBLEConfigEntry", SimpleNamespace(runtime_data=device)),
            cast("AddEntitiesCallback", entities.extend),
        )

    charging = [args for args in entities if args[1] == "Charging Status"]
    assert len(charging) == 1
    assert charging[0][3] == "charging_status"
    assert charging[0][5] == CHARGING_STATUS_C300_STRINGS
    assert charging[0][5][2] == "Discharging"

    input_limits = [
        args for args in entities if args[1] == "AC Power Input Limit"
    ]
    assert len(input_limits) == 1
    assert input_limits[0][3] == "ac_charging_power"


@pytest.mark.parametrize(
    ("charging_status", "expected"),
    [
        (ChargingStatus.IDLE, "Idle"),
        (ChargingStatus.DISCHARGING, "Discharging"),
        (ChargingStatus.CHARGING, "Charging"),
    ],
)
def test_legacy_f2000_charging_status_rendering(
    charging_status: ChargingStatus, expected: str,
) -> None:
    """Translate actual library enum values into the expected HA sensor state."""
    device = SimpleNamespace(
        name="Test original F2000",
        address="AA:BB:CC:DD:EE:FF",
        available=True,
        charging_status=charging_status,
    )
    sensor = SolixSensorEntity(
        cast("F2000Legacy", device),
        "Charging Status",
        cast("str", None),  # Enum sensors do not use a unit
        "charging_status",
        SensorDeviceClass.ENUM,
        CHARGING_STATUS_C300_STRINGS,
        None,
    )
    assert sensor.native_value == expected
