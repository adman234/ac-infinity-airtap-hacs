from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify

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
    async_add_entities([ACInfinityPowerSwitch(data.coordinator, data.device)])


class ACInfinityPowerSwitch(
    ActiveBluetoothCoordinatorEntity[ACInfinityDataUpdateCoordinator], SwitchEntity
):
    _attr_device_class = SwitchDeviceClass.SWITCH
    _attr_has_entity_name = True
    _attr_name = "Power"

    def __init__(
        self,
        coordinator: ACInfinityDataUpdateCoordinator,
        device: ACInfinityDevice,
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._attr_unique_id = f"{self._device.address}_power"
        self._attr_device_info = DeviceInfo(
            name=device.name,
            model=DEVICE_MODEL[device.state.type],
            manufacturer=MANUFACTURER,
            sw_version=device.state.version,
            connections={(dr.CONNECTION_BLUETOOTH, device.address)},
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._device.turn_on()
        self._update_attrs()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._device.turn_off()
        self._update_attrs()
        self.async_write_ha_state()

    @callback
    def _update_attrs(self) -> None:
        self._attr_is_on = self._device.is_on

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_attrs()
        super()._handle_coordinator_update()
