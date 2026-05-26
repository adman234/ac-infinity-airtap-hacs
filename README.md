# AC Infinity Airtap — Home Assistant Integration

Home Assistant custom integration for Bluetooth Low Energy (BLE) control of [AC Infinity Airtap](https://acinfinity.com/register-booster-fans/) series register fans.

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
