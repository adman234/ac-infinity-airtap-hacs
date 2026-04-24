from __future__ import annotations

import math
from collections.abc import Awaitable, Callable
from typing import Optional

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify
from homeassistant.util.percentage import (percentage_to_ranged_value,
                                           ranged_value_to_percentage)

from .const import DEVICE_MODEL, DOMAIN, MANUFACTURER
from .coordinator import (ACInfinityDataUpdateCoordinator,
                          ActiveBluetoothCoordinatorEntity)
from .device import ACInfinityDevice
from .models import ACInfinityData

SPEED_RANGE = (1, 10)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data: ACInfinityData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        SpeedNumber(data.coordinator, data.device, "Min Speed",
                    lambda d: d.min_speed, ACInfinityDevice.async_set_min_speed),
        SpeedNumber(data.coordinator, data.device, "Max Speed",
                    lambda d: d.max_speed, ACInfinityDevice.async_set_max_speed),
    ])


class SpeedNumber(
    ActiveBluetoothCoordinatorEntity[ACInfinityDataUpdateCoordinator], NumberEntity
):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_native_step = 10.0

    def __init__(
        self,
        coordinator: ACInfinityDataUpdateCoordinator,
        device: ACInfinityDevice,
        name: str,
        get_value: Callable[[ACInfinityDevice], Optional[int]],
        async_set_value: Callable[[ACInfinityDevice, int], Awaitable[None]],
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._attr_name = name
        self._attr_unique_id = f"{self._device.address}_number_{slugify(name)}"
        self._attr_device_info = DeviceInfo(
            name=device.name,
            model=DEVICE_MODEL[device.state.type],
            manufacturer=MANUFACTURER,
            sw_version=device.state.version,
            connections={(dr.CONNECTION_BLUETOOTH, device.address)},
        )
        self._get_value = get_value
        self._async_set_value = async_set_value

    async def async_set_native_value(self, value: float) -> None:
        await self._async_set_value(self._device, math.ceil(percentage_to_ranged_value(SPEED_RANGE, value)))
        self._update_attrs()
        self.async_write_ha_state()

    @callback
    def _update_attrs(self) -> None:
        raw = self._get_value(self._device)
        self._attr_native_value = None if raw is None else ranged_value_to_percentage(SPEED_RANGE, raw)

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_attrs()
        super()._handle_coordinator_update()
