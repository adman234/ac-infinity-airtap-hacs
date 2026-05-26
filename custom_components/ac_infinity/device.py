from __future__ import annotations

import asyncio
import dataclasses
import logging
from dataclasses import dataclass
from typing import Optional

from ac_infinity_ble import ACInfinityController, DeviceInfo
from ac_infinity_ble.const import CallbackType, MANUFACTURER_ID
from ac_infinity_ble.protocol import parse_manufacturer_data
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak.exc import BleakDBusError
from bleak_retry_connector import BleakError, retry_bluetooth_connection_error

from .const import FAMILY_E_MODELS

_BLEAK_BACKOFF_TIME = 0.25
_DEFAULT_ATTEMPTS = 3

_LOGGER = logging.getLogger(ACInfinityController.__module__)
_MIN_SECONDS_BETWEEN_POLLS = 30


@dataclass
class DeviceInfoEx(DeviceInfo):
    @staticmethod
    def create(device_info: DeviceInfo) -> DeviceInfoEx:
        return DeviceInfoEx(**device_info.__dict__)


class ACInfinityDevice(ACInfinityController):
    _config_changed_since_last_update = False

    def __init__(
        self,
        ble_device: BLEDevice,
        state: DeviceInfoEx | None = None,
        advertisement_data: AdvertisementData | None = None,
    ):
        super().__init__(
            ble_device=ble_device,
            state=state,
            advertisement_data=advertisement_data,
        )

        if type(self._state) is DeviceInfo:
            self._state = DeviceInfoEx(**self._state.__dict__)

    @retry_bluetooth_connection_error(_DEFAULT_ATTEMPTS)
    async def _send_command_locked(self, command: bytes) -> bytes | None:
        # The base class retry decorator calls this directly on retry without
        # reconnecting first, so _client can be None. Re-ensure connection here.
        await self._ensure_connected()
        try:
            return await self._execute_command_locked(command)
        except BleakDBusError as ex:
            await asyncio.sleep(_BLEAK_BACKOFF_TIME)
            _LOGGER.debug(
                "%s: RSSI: %s; Backing off %ss; Disconnecting due to error: %s",
                self.name, self.rssi, _BLEAK_BACKOFF_TIME, ex,
            )
            await self._execute_disconnect()
            raise
        except BleakError as ex:
            _LOGGER.debug(
                "%s: RSSI: %s; Disconnecting due to error: %s", self.name, self.rssi, ex
            )
            await self._execute_disconnect()
            raise

    def set_ble_device_and_advertisement_data(
        self, ble_device: BLEDevice, advertisement_data: AdvertisementData
    ) -> None:
        self._ble_device = ble_device
        self._advertisement_data = advertisement_data
        info = parse_manufacturer_data(
            advertisement_data.manufacturer_data[MANUFACTURER_ID]
        )
        self._state = dataclasses.replace(
            self._state, **{k: v for k, v in dataclasses.asdict(info).items() if v is not None}
        )
        self._fire_callbacks(CallbackType.ADVERTISEMENT)

    @property
    def speed(self) -> Optional[int]:
        return self._state.fan

    @property
    def temperature(self) -> Optional[float]:
        return self._state.tmp

    @property
    def humidity(self) -> Optional[float]:
        return self._state.hum

    @property
    def vpd(self) -> Optional[float]:
        return self._state.vpd

    @property
    def min_speed(self) -> Optional[int]:
        return self._state.level_off

    @property
    def max_speed(self) -> Optional[int]:
        return self._state.level_on

    @property
    def state(self) -> DeviceInfoEx:
        return self._state

    def update_needed(self, seconds_since_last_update: Optional[float | int]) -> bool:
        return (self._config_changed_since_last_update or
                seconds_since_last_update is None or seconds_since_last_update > _MIN_SECONDS_BETWEEN_POLLS)

    async def update(self) -> None:
        await self._ensure_connected()
        try:
            _LOGGER.debug("%s: Updating model data", self.name)
            command = self._protocol.get_model_data(self.state.type, 0, self.sequence)
            if data := await self._send_command(command):
                if len(data) < 19:
                    _LOGGER.debug(
                        "%s: Skipping update; data too short (%s): %s",
                        self.name, len(data), data.hex()
                    )
                else:
                    self.state.work_type = data[12]
                    self.state.level_off = data[15]
                    self.state.level_on = data[18]
                    self._config_changed_since_last_update = False
                    self._fire_callbacks(CallbackType.UPDATE_RESPONSE)
        finally:
            await self._execute_disconnect()

    async def async_set_power(self, enabled: bool) -> None:
        if enabled:
            await self.turn_on()
        else:
            await self.turn_off()

    async def async_set_min_speed(self, value: int) -> None:
        if value not in range(0, 11):
            raise ValueError("value must be between 0 and 10")

        _LOGGER.debug("%s: Setting min speed to %s", self.name, value)

        command = [17, 1, value]
        if self.state.type in FAMILY_E_MODELS:
            command += [255, 0]
        command = self._protocol._add_head(command, 3, self.sequence)

        await self._ensure_connected()
        try:
            await self._send_command(command)
            self.state.level_off = value
            self._config_changed_since_last_update = True
        finally:
            await self._execute_disconnect()

    async def async_set_max_speed(self, value: int) -> None:
        if value not in range(0, 11):
            raise ValueError("value must be between 0 and 10")

        _LOGGER.debug("%s: Setting max speed to %s", self.name, value)

        command = [18, 1, value]
        if self.state.type in FAMILY_E_MODELS:
            command += [255, 0]
        command = self._protocol._add_head(command, 3, self.sequence)

        await self._ensure_connected()
        try:
            await self._send_command(command)
            self.state.level_on = value
            self._config_changed_since_last_update = True
        finally:
            await self._execute_disconnect()
