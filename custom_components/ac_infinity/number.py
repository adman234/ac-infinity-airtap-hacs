from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DEVICE_MODEL, DOMAIN, MANUFACTURER
from .coordinator import (ACInfinityDataUpdateCoordinator,
                          ActiveBluetoothCoordinatorEntity)
from .device import ACInfinityDevice
from .models import ACInfinityData


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data: ACInfinityData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FanSpeedNumber(data.coordinator, data.device)])


class FanSpeedNumber(
    ActiveBluetoothCoordinatorEntity[ACInfinityDataUpdateCoordinator], NumberEntity
):
    _attr_has_entity_name = True
    _attr_name = "Speed"
    _attr_native_min_value = 1.0
    _attr_native_max_value = 10.0
    _attr_native_step = 1.0

    def __init__(
        self,
        coordinator: ACInfinityDataUpdateCoordinator,
        device: ACInfinityDevice,
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._attr_unique_id = f"{self._device.address}_speed"
        self._attr_device_info = DeviceInfo(
            name=device.name,
            model=DEVICE_MODEL[device.state.type],
            manufacturer=MANUFACTURER,
            sw_version=device.state.version,
            connections={(dr.CONNECTION_BLUETOOTH, device.address)},
        )

    async def async_set_native_value(self, value: float) -> None:
        await self._device.async_set_speed(int(value))
        self._update_attrs()
        self.async_write_ha_state()

    @callback
    def _update_attrs(self) -> None:
        self._attr_native_value = self._device.speed_setting

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_attrs()
        super()._handle_coordinator_update()
