"""Regression checks for the original 767/F2000 (A1780) legacy model.

These tests exercise Home Assistant sensor registration without BLE hardware.
They require a SolixBLE build exporting F2000Legacy.
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from SolixBLE import F2000Legacy

from custom_components.solix_ble import get_power_station_class
from custom_components.solix_ble.const import Models
from custom_components.solix_ble.sensor import (
    CHARGING_STATUS_C300_STRINGS,
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
    entities: list[tuple] = []

    with patch(
        "custom_components.solix_ble.sensor.SolixSensorEntity",
        side_effect=lambda *args, **kwargs: args,
    ):
        await async_setup_entry(
            None,  # hass is not used by this sensor factory
            SimpleNamespace(runtime_data=device),
            entities.extend,
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
