# ProVent RC7 Premium Home Assistant Integration

![ProVent logo](logo.png)

Custom Home Assistant integration that speaks the same WebManipulator API the mobile app uses. It polls `GET /api/getdata.php` to read SQLite-buffered Modbus values (JSON) and exposes them as HA sensors, while mirroring every mobile-app command through `POST /api/savedata.php`.

## Architecture & Communication
1. **Polling data**: The integration uses `Ha`'s `DataUpdateCoordinator` to POST `variable[]=all` to `/api/getdata.php`. The WebManipulator returns a JSON map (e.g. `"tmp"`, `"dat"`, `"spd"`, `"nag"`, `"chl"`, etc.) that already contains decoded values from the onboard SQLite buffer, which itself is maintained by the Modbus-RTU daemon.
2. **Command execution**: When you need to change the fan speed, bypass, season, etc., the mobile app posts `data=...` strings to `/api/savedata.php`. We expose the same mechanism via the `provent.send_command` service so HA can send `"spd:b2"`, `"bps:ta"`, `"nag:T25"`, etc.
3. **Decoding the payload**: The sensors parse the native JSON fields using the exported Modbus register mapping (`opis-rejestrow-modbus-s6.pdf`). For example, `tmp` contains five groups of four temperatures each, `dat` includes the current timestamp, `spd` packs fan speed + flags + ventilation timer, and `nag`/`chl` parse heating/cooling setpoint, measured temperature, and status letters derived from register HR 13/HR 14/IR 122.

## Requirements
- A ProVent RC7 premium (S6) or compatible WebManipulator-based device reachable on your LAN.
- The `/api/getdata.php`/`/api/savedata.php` endpoints accessible without additional authentication.
- Home Assistant 2023.12 or newer (tested on 2026.2.3, which includes the typing hints and coordinator helpers used by this integration).

## Installation
### Via HACS
1. In HACS go to **Integrations > Explore & add repositories**.
2. Paste `https://github.com/deltasystems-pl/ha-provent-rc7-premium` and set the category to **Integration**.
3. Install the repository, then restart Home Assistant.
4. After restart, add the integration via **Settings > Devices & Services > Add Integration > ProVent RC7 Premium**.
   The 1.0.1 release ZIP already contains `custom_components/provent/` along with the documentation and assets, so HACS deploys the integration directly under your HA `custom_components` directory.
   HACS also inspects the root-level `manifest.json` (included for compatibility) before it copies `custom_components/provent/` into HA.

### Manual installation
1. Copy the `custom_components/provent/` folder from this repository into `<config>/custom_components/provent/`.
2. Verify the integration folder includes `manifest.json`, `services.yaml`, and the HA components; the HACS metadata file is optional when you install manually.
3. Restart Home Assistant and add the integration via the UI as described above.

## Configuration
When you add the integration you must provide:
- **Host**: IP or hostname of the WebManipulator (e.g., `192.168.88.98`).
- **Port**: Usually `80`, unless you configured the web UI on another port.
- **API Path**: Defaults to `/api`. If you moved the PHP scripts elsewhere, adjust accordingly.
- **Use SSL**: Enable if you configured HTTPS on the WebManipulator.
- **Name**: Friendly label (defaults to `ProVent RC7 Premium`).

After setup, the integration keeps polling the device every 20 seconds.

## Available entities (sensors)
| Entity Key | Description |
|------------|-------------|
| `dat` | Control timestamp (native HA timestamp sensor). |
| `spd_speed` | Fan speed setting (0–4). |
| `spd_flags` | Raw flag/letter string from `spd` (manual/program, window, etc.). |
| `spd_remaining` | Minutes remaining on an active ventilation boost. |
| `flt` | Days until filter replacement (or filter bitmask). |
| `bps` | Hex-encoded bypass position/state. |
| `gwc` | Hex-encoded GWC position/state (if configured). |
| `sez_current` | Season currently active (`winter`, `summer`, etc.). |
| `sez_mode` | Season mode (`auto`, `forced_winter`, `forced_summer`). |
| `stn` | System state code (0 = normal). |
| `asc` | Global alarm/state letter. |
| `iaw` | Active info/alarm/ warning list (comma-separated). |
| `nag_setpoint` | Heating setpoint (°C). |
| `nag_temp` | Heating measured temperature (°C). |
| `nag_status` | Heating status suffix (e.g., `wuW`). |
| `chl_setpoint` | Cooling setpoint (°C). |
| `chl_temp` | Cooling measured temperature (°C). |
| `chl_status` | Cooling status suffix (e.g., `wuW`). |
| `elf` | Electrofilter raw status string (conditional on CleanR). |
| `tmp_t1a` … `tmp_t5d` | The 20 temperature channels described in the Modbus docs. Each sensor reports a float or `null` when the probe is absent. |

The integration provides a sensor per description above, with an HA-friendly name and unit when applicable.

## Additional control entities
The integration also exposes writable entities (when the related feature exists on the unit):
- **Fan**: one HA fan entity with speed percentages (mapped to ProVent gear `0..4`) and preset mode (`auto`/`manual`).
- **Selects**: ventilation mode (`auto`/`manual`), airflow mode, season override, bypass mode, GWC mode.
- **Numbers**: fan speed setpoint (`0..4`), heating setpoint (`4..35°C`), cooling setpoint (`4..35°C`).
- **Switches**: ventilation boost, humidity control, CO2 control, anti-smog shield (when available in `elf` payload).

## Fancy "Quick Control" widget
A ready Lovelace widget is included at:
- `examples/lovelace_provent_widget.yaml`

It gives one compact control block with:
- fan on/off + speed + preset mode
- boost/humidity/CO2/anti-smog toggles
- airflow/season/bypass/GWC selectors
- heating/cooling setpoint controls
- key live status rows

Import it as a **Manual card** and replace the example entity IDs with your own.

## Services
### `provent.send_command`
- **Description**: Sends arbitrary `data=` commands to `/api/savedata.php`, identical to what the official app does for fan speed, bypass, season, boost, etc.
- **Fields**:
  - `command` (required): e.g., `"spd:b2"` to set fan speed to 2, `"bps:ta"` to toggle bypass, `"nag:T25"` for heating setpoint, `"sez:la"` for force summer, etc.
  - `entry_id` (optional): Specify the specific config entry to route the command if you have multiple ProVent installations.
  - `validate` (optional, default `true`): validates known command groups and value ranges before sending to the device.

Use `provent.send_command` in automations/scripts for manual overrides or to reflect UI interactions.

## Developing & Troubleshooting
- Run `python -m compileall ha-provent` to verify imports/typing.
- Check HA logs for `provent` domain entries; network errors typically mean the device is unreachable or the API path is wrong.
- If you want to reverse engineer more commands, watch the WebManipulator GUI’s network tab for `getdata.php`/`savedata.php` calls.
- Use the Modbus register map (`opis-rejestrow-modbus-s6.pdf`) to decode additional fields or extend the integration with switches/number entities (fan boost, heating modes, custom commands).
