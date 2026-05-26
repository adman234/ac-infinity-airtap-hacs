# AC Infinity Airtap — Home Assistant Integration

Home Assistant custom integration for Bluetooth Low Energy (BLE) control of [AC Infinity Airtap](https://acinfinity.com/register-booster-fans/) series register fans.

## Changes in this fork

- **Simplified entities:** removed auto/climate mode controls; temperature is now a read-only sensor rather than part of a climate device
- **Single fan speed:** replaced separate min/max speed controls with one speed setting (1–10) that the device holds across power cycles
- **Stability fixes:** resolved a 500 error during device discovery caused by nearby non-AC-Infinity Bluetooth devices, an assertion error on switch toggle, and a config entry serialization issue that could cause the integration to fail after a restart

## Troubleshooting

To enable debug logging, add the following to your [logger config](https://www.home-assistant.io/integrations/logger/):

```yaml
logger:
  default: info
  logs:
    ac_infinity_ble: debug
    custom_components.ac_infinity: debug
```

## Credits

Built on work by [mtsphere](https://github.com/mtsphere/ac-infinity-airtap-hacs) and originally [Jason Hunter (hunterjm)](https://github.com/hunterjm/ac-infinity-hacs). Uses the [ac-infinity-ble](https://github.com/hunterjm/ac-infinity-ble/) library.
