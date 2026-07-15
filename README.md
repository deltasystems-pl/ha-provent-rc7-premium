<p align="center">
  <img src="https://raw.githubusercontent.com/deltasystems-pl/ha-provent-rc7-premium/main/logo.png" alt="ProVent RC7 Premium" height="80" />
</p>

<h1 align="center">ProVent RC7 Premium — Home Assistant Integration</h1>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Custom" /></a>
  <img src="https://img.shields.io/badge/version-1.0.5-informational.svg" alt="Version" />
  <img src="https://img.shields.io/badge/Home%20Assistant-2023.12%2B-41BDF5.svg?logo=home-assistant&logoColor=white" alt="Home Assistant" />
  <img src="https://img.shields.io/badge/IoT%20class-local%20polling-success.svg" alt="Local polling" />
  <img src="https://img.shields.io/badge/license-see%20LICENSE-lightgrey.svg" alt="License" />
</p>

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=deltasystems-pl&amp;repository=ha-provent-rc7-premium&amp;category=integration">
    <img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open your Home Assistant instance and open this repository inside the Home Assistant Community Store." />
  </a>
</p>

> **Install via HACS:** click the button above (or in HACS → ⋮ → *Custom repositories*, add `https://github.com/deltasystems-pl/ha-provent-rc7-premium` as category **Integration**), download, then **restart Home Assistant** and add it via *Settings → Devices & Services → Add Integration → ProVent RC7 Premium*.

Local **Pro-Vent RC7 premium (S6) / RC7 home (S8)** recuperator integration for Home Assistant. It speaks the same WebManipulator API the mobile app uses — polling `GET /api/getdata.php` to read the SQLite-buffered Modbus values (JSON) and exposing them as Home Assistant entities, while mirroring every mobile-app command through `POST /api/savedata.php`. 100 % local, no cloud.

### Highlights
- 🌀 **Fan** entity (gear 0–4, auto/manual preset) + a precise fan-speed number.
- 💨 **Ventilation boost** — the unit's *airing* (wietrzenie) function, reflecting the live countdown.
- 🎛️ **Selects** — ventilation mode, airflow direction, season override, bypass, GWC.
- 🌡️ **Climate** — heating/cooling setpoints and measured temperatures.
- 🧰 **Diagnostics** — filter days, alarms, system/heating/cooling status, 20 exchanger temperatures.
- 🧩 **Raw `provent.send_command` service** for anything not exposed as an entity.

> **Capability auto-detection.** Entities are created only for features the unit actually has, and controls the hardware lacks (humidity/CO₂ sensors, GWC, secondary heater/cooler, CleanR electrofilter/anti-smog) report **unavailable** instead of appearing as phantom controls. So a bare unit shows fewer/greyed-out entities — that's expected, not a bug.

## Supported devices
- **Pro-Vent RC7 premium (S6)** and **RC7 home (S8)** automation, and compatible **WebManipulator**-based central units (firmware variants such as S6/S8/GC2 all expose the same `getdata.php` / `savedata.php` API).
- The device must be reachable on your LAN with `/api/getdata.php` and `/api/savedata.php` accessible **without additional authentication**.

## Requirements
- Home Assistant **2023.12** or newer (developed/tested through **2026.7**). On **2026.3+** the integration's bundled logo is shown automatically via the local brands proxy.
- Network access from HA to the WebManipulator (default HTTP port 80).

## Installation

### Via HACS (recommended)
1. Use the **Add-to-HACS** button above, or in HACS add `https://github.com/deltasystems-pl/ha-provent-rc7-premium` as a **Custom repository** with category **Integration**.
2. Download the integration and **restart Home Assistant**.
3. Add it via **Settings → Devices & Services → Add Integration → ProVent RC7 Premium**.

HACS installs the `custom_components/provent/` folder from the latest tagged release, so it always tracks a versioned release rather than a raw commit.

### Manual installation
1. Copy `custom_components/provent/` from this repository into `<config>/custom_components/provent/`.
2. Restart Home Assistant and add the integration via the UI as above.

## Configuration
| Field | Default | Notes |
|-------|---------|-------|
| **Host** | — | IP or hostname of the WebManipulator, e.g. `192.168.1.50`. |
| **Port** | `80` | HTTP port of the web module. |
| **API Path** | `/api` | Path to the PHP scripts. |
| **Use SSL** | off | Enable only if the module serves HTTPS. |
| **Name** | `ProVent RC7 Premium` | Friendly label / device name. |

After setup the integration polls the device every **20 seconds**. The device card shows the manufacturer, model and a **Visit device** link to the WebManipulator web UI.

## Entities

### Controls
| Entity | Type | Range / options | Notes |
|--------|------|-----------------|-------|
| Fan | `fan` | gear 0–4 (percentage), preset `auto`/`manual` | Speed maps to ProVent gear 0..4 (25 % steps). |
| Fan Speed Setpoint | `number` | 0–4 | Authoritative discrete gear control. |
| Ventilation Boost | `switch` | on/off | Starts/stops *airing* (register 10). On while the timer counts down. |
| Humidity Control | `switch` | on/off | Only when a humidity sensor is fitted, otherwise unavailable. |
| CO₂ Control | `switch` | on/off | Only when a CO₂ sensor is fitted, otherwise unavailable. |
| Anti-Smog Shield | `switch` | on/off | Only with a CleanR electrofilter. |
| Ventilation Mode | `select` | `auto`, `manual` | Program (daily schedule) vs manual gear. |
| Airflow Mode | `select` | `both`, `supply_only`, `extract_only` | Depends on the unit's fan-shutdown capability. |
| Season Override | `select` | `auto`, `forced_winter`, `forced_summer` | |
| Bypass Mode | `select` | `auto`, `forced_on`, `forced_off` | Only with a bypass. |
| GWC Mode | `select` | `auto`, `forced_on`, `forced_off` | Only with a ground heat exchanger. |
| Heating Setpoint | `number` | 4–35 °C | Secondary heater/cooler device 1. |
| Cooling Setpoint | `number` | 4–35 °C | Secondary heater/cooler device 1. |

### Sensors
| Entity key | Description | Category |
|------------|-------------|----------|
| `spd_speed` | Fan gear (0–4). | — |
| `spd_remaining` | Minutes remaining on the active airing/boost (0 when off). | — |
| `flt` | Days until filter replacement (or, with pressostats, a filter bitmask). | — |
| `bps` | Bypass position/state. | — |
| `gwc` | GWC position/state (if configured). | — |
| `sez_current` | Active season (`winter`/`summer`). | — |
| `nag_setpoint` / `nag_temp` | Heating setpoint / measured temperature (°C). | — |
| `chl_setpoint` / `chl_temp` | Cooling setpoint / measured temperature (°C). | — |
| `tmp_t1a` … `tmp_t5d` | 20 exchanger temperature channels (Modbus IR 124–143); `null` when the probe is absent. | — |
| `dat` | Control timestamp. | Diagnostic |
| `spd_flags` | Raw flag string (mode/airflow/humidity/CO₂ letters). | Diagnostic |
| `sez_mode` | Season mode (`auto`/`forced_winter`/`forced_summer`). | — |
| `stn` | System state code (`0` = normal). | Diagnostic |
| `asc` | Global alarm/state letter (`N` = none). | Diagnostic |
| `iaw` | Active info/alarm/warning codes. | Diagnostic |
| `nag_status` / `chl_status` | Heating / cooling status suffix. | Diagnostic |
| `elf` | Electrofilter raw status string (CleanR only). | Diagnostic |

Diagnostic entities are grouped under the device page's **Diagnostic** section to keep the primary controls uncluttered.

## `provent.send_command` service
Every control above is exposed as an entity, but `provent.send_command` lets you send **any** raw command the mobile app can — useful for automations, unmapped features, or scripting.

| Field | Required | Description |
|-------|----------|-------------|
| `command` | yes | Command string, e.g. `spd:b2`. |
| `entry_id` | no | Target a specific ProVent device if more than one is configured. |
| `validate` | no (default `true`) | Validate the group/value range before sending. |

### Command reference
Format is `group:payload`. Common commands:

| Command | Effect |
|---------|--------|
| `spd:b0` … `spd:b4` | Set fan gear 0–4. |
| `spd:ta` / `spd:tm` | Ventilation mode auto (program) / manual. |
| `spd:po` / `spd:pn` / `spd:pw` | Airflow both / supply-only / extract-only. |
| `spd:w1` / `spd:w0` | Airing (boost) on / off. |
| `spd:h1` / `spd:h0` | Humidity control on / off *(if fitted)*. |
| `spd:c1` / `spd:c0` | CO₂ control on / off *(if fitted)*. |
| `bps:ta` / `bps:tz` / `bps:tw` | Bypass auto / forced-on / forced-off. |
| `gwc:ta` / `gwc:tz` / `gwc:tw` | GWC auto / forced-on / forced-off. |
| `sez:sa` / `sez:sz` / `sez:sl` | Season auto / winter / summer. |
| `nag:T4` … `nag:T35` | Heating setpoint °C (prefix `2` targets device 2, e.g. `nag:2T22`). |
| `chl:T4` … `chl:T35` | Cooling setpoint °C. |
| `asc:r` | Clear an active emergency stop. |
| `elf:t1` / `elf:t0`, `elf:f0..f3` | Anti-smog on/off, electrofilter mode *(CleanR only)*. |

The complete reverse-engineered command map (including zones, date/time and electrofilter sub-commands) is in [`FUTURE.md`](FUTURE.md), and the raw register semantics in [`opis-rejestrow-modbus-s6.pdf`](opis-rejestrow-modbus-s6.pdf).

## Example: stop ventilation while a window is open
Pause the recuperator when a contact opens and restore the previous gear/boost when everything closes:

```yaml
# Stop when a window opens
automation:
  - alias: ProVent – window open, stop
    triggers:
      - trigger: state
        entity_id: binary_sensor.window_contact
        to: "on"
    conditions:
      - "{{ is_state('fan.provent_rc7_premium_fan','on') or is_state('switch.provent_rc7_premium_ventilation_boost','on') }}"
    actions:
      - action: scene.create
        data: { scene_id: provent_backup, snapshot_entities: [number.provent_rc7_premium_fan_speed_setpoint, switch.provent_rc7_premium_ventilation_boost] }
      - action: number.set_value
        target: { entity_id: number.provent_rc7_premium_fan_speed_setpoint }
        data: { value: 0 }

  - alias: ProVent – window closed, restore
    triggers:
      - trigger: state
        entity_id: binary_sensor.window_contact
        to: "off"
    actions:
      - action: scene.turn_on
        target: { entity_id: scene.provent_backup }
```

> Tip: the **fan-speed setpoint number** (not the fan percentage) is the most reliable way to stop/start the unit — writing `0` stops it, writing the previous gear restores it.

## Lovelace quick-control widget
A ready-made compact control card is included at [`examples/lovelace_provent_widget.yaml`](examples/lovelace_provent_widget.yaml) — fan on/off + speed + preset, boost/humidity/CO₂/anti-smog toggles, airflow/season/bypass/GWC selectors, heating/cooling setpoints and key live-status rows. Import it as a **Manual card** and replace the example entity IDs with your own.

## How it works
1. **Read** — a `DataUpdateCoordinator` POSTs `variable[]=all` to `/api/getdata.php`. The WebManipulator returns a JSON map (`tmp`, `dat`, `spd`, `nag`, `chl`, `bps`, `gwc`, `sez`, `elf`, `flt`, `stn`, `asc`, `iaw`, …) decoded from the onboard SQLite buffer that the Modbus-RTU daemon maintains.
2. **Write** — commands are POSTed as `data=<group:payload>` to `/api/savedata.php`, which the daemon applies over Modbus RTU.
3. **Decode** — packed fields are parsed per the Modbus map. The `spd` field, for example, packs `gear + mode + airflow + humidity + CO₂ + airing-duration [+ airing-remaining]`; the trailing digits are the configured airing *duration* and a live countdown is appended only while airing is active. `nag`/`chl` carry setpoint + measured temperature + status letters. See [`FUTURE.md`](FUTURE.md) for the exact string grammars.

## Troubleshooting
- **Some entities are `unavailable`.** Expected when the hardware lacks that feature (no humidity/CO₂ sensor, no GWC/bypass, no secondary heater/cooler, no CleanR). Capability is auto-detected from the device payload.
- **Cannot connect / everything unavailable.** Check the host, port and API path, and that `getdata.php`/`savedata.php` are reachable without a login. Watch the HA log for the `provent` domain.
- **A command has no effect.** Confirm the feature exists on your unit and the value is in range; try it manually with `provent.send_command` and `validate: true`.
- **Reverse-engineering more commands.** Watch the WebManipulator web UI's network tab for `getdata.php`/`savedata.php` calls, or read `FUTURE.md` / the Modbus PDF.

## Contributing / development
- Validate syntax with `python -m compileall custom_components/provent`.
- The integration is pure `local_polling` with no external requirements.
- Icons/logo live in `custom_components/provent/brand/` and are served by Home Assistant 2026.3+ via its local brands proxy (custom integrations ship their own brand images now — they are no longer submitted to `home-assistant/brands`).
- Releases and changelog: <https://github.com/deltasystems-pl/ha-provent-rc7-premium/releases>.

## License
See [LICENSE](LICENSE).
