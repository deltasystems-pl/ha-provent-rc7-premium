# ProVent API + Modbus RTU Reverse Engineering Notes

Last verified on device: 2025-03-18 (WebManipulator host `192.168.88.98`, DietPi v7.9.4).

## 1) End-to-end write path (confirmed)

Web UI and HA both use:
- `POST /api/savedata.php` with form field `data=<comma-separated commands>`

On device this becomes:
1. `savedata.php` writes each command as a new line into FIFO `/tmp/wm_pipe`.
2. Python daemon `/usr/local/bin/wm-pth-new/main.py` (`ThreadPipe_run`) reads FIFO and pushes command source `WM` into `mb.queue_cmd`.
3. `gc_new_values()` in `/usr/local/bin/wm-pth-new/cmgc.py` parses `grp:varval` commands and converts them to an internal frame:
   - `['V', code, value, code, value, ...]`
4. Main loop sends resulting frame to central unit over message queue (`wm2cu`), then central unit applies it over Modbus RTU side.

## 2) End-to-end read path (confirmed)

Read API:
- `POST /api/getdata.php` with `variable[]=all` (or specific keys)

Flow:
1. Web/API reads SQLite (`/tmp/provent_sqlite3.db`, table `variable`).
2. Daemon continuously updates `variable` table from CU/Modbus decoded frames.
3. `getdata.php` returns JSON string under `all`.

Example live payload:
```json
{
  "all": "{\"tmp\":\"+13.4,+15.4,...\",\"dat\":\"41737060326\",\"nag\":\"21+23.2wuW\",\"chl\":\"13+23.3wuW\",\"sez\":\"za\",\"bps\":\"0a\",\"gwc\":\"0a\",\"spd\":\"1mo--15\",\"flt\":74,\"asc\":\"N\",\"stn\":\"0\",\"iaw\":[],\"elf\":\"za1221005----------\"}"
}
```

## 3) Command grammar accepted by `savedata.php`

General format:
- `group:command`
- multiple commands in one request: `data=cmd1,cmd2,cmd3`

Confirmed groups:
- `spd` ventilation
- `bps` bypass
- `sez` season
- `gwc` ground exchanger
- `nag` heater
- `chl` cooler
- `str` zones
- `dat` date/time
- `asc` emergency/test reset
- `elf` electrofilter

## 4) High-value command map (web UI -> internal `V` code)

From `/var/www/js/ViewModels/*.js` + `/usr/local/bin/wm-pth-new/cmgc.py` + `cm_set_codes.py`.

### Ventilation (`spd`)
- `spd:b<0..4>` -> set fan gear (`CM_SET_SPD_GEAR = 3`)
- `spd:t[a|m]` -> auto/manual (`CM_SET_SPD_MODE = 4`, values 1/0)
- `spd:p[o|w]` -> vent mode (`CM_SET_SPD_VENT = 5`, values 1/0)
- `spd:w[0|1]` -> boost on/off (`CM_SET_SPD_AIR = 6`)
- `spd:h[0|1]` -> humidity control (`CM_SET_SPD_HMD = 27`)
- `spd:c[0|1]` -> CO2 control (`CM_SET_SPD_CO2 = 28`)

### `spd` read-back grammar (confirmed on device, GC2 firmware `cmgc.py`)

The daemon composes `spd` in `cmgc.py` (`gc_new_values`). Exact layout:

```
spd = gear(1 digit 0-4)
    + either 'c'                       -> CO-alarm state, nothing else follows
      or:
        mode      (1)  'a' auto / 'm' manual
        airflow   (1)  'o' / 'w'
        humidity  (1)  '1'/'0'  ('-' when no humidity sensor is fitted)
        co2       (1)  '1'/'0'  ('-' when no CO2 sensor is fitted)
        duration  (2 digits)  configured airing time (frame[26]&0x7F) -- ALWAYS present
        remaining (2 digits)  live airing countdown -- ONLY appended while airing runs
```

Examples: `4mo--15` = gear 4, manual, both fans, no hum/co2 sensor, airing duration 15, **airing off**;
`4mo--1513` = same but **airing on**, 13 min left (Modbus reg 10 read); `4c` = CO alarm.

Key gotchas (were bugs in the integration, fixed in 1.0.2):
- The trailing 2 digits when airing is OFF are the **duration setting**, NOT remaining
  (reg 10 reads 0 when inactive). Only treat digits beyond the duration as remaining, else
  the boost switch reads permanently on.
- Humidity/CO2 are positional flags (`1`/`0`/`-`), never letters `h`/`c`; a `-` means the
  sensor is not fitted, so the corresponding switch should be unavailable, not "off".
- `cfg['spd']` (e.g. `24N--`) advertises capability: `2`,maxgear`4`,airflow-off`N/W/O/-`,
  humidity`H/-`,co2`C/-`.

### Bypass / season / GWC
- `bps:t[a|z|w]` -> bypass mode (`CM_SET_BPS_MODE = 10`, values 2/1/0)
- `sez:s[a|z|l]` -> season mode (`CM_SET_SEASON_MODE = 9`, values 2/1/0)
- `gwc:t[a|z|w]` -> GWC mode (`CM_SET_GHX_MODE = 12`, values 2/1/0)

### Heating / cooling
- `nag:t[a|m|w]` and `chl:t[a|m|w]` -> mode (`CM_SET_HTCLx_MODE`)
- `nag:T<temp>` and `chl:T<temp>` -> setpoint (`CM_SET_HTCLx_T`)
- On multi-circuit units: `nag:1t...`, `nag:2t...`, `nag:1T...`, `nag:2T...` (same for `chl`)

### Date/time
- `dat:d<0..6>` day of week
- `dat:g<0..23>` hour
- `dat:m<0..59>` minute
- `dat:D<1..31>` day of month
- `dat:M<1..12>` month
- `dat:R<yy>` year suffix

### Zones
- `str:<zone>s[0|1]` zone state
- `str:<zone>t[r|a]` zone mode

### Electrofilter
- `elf:f<n>` mode
- `elf:J<n>` day ionization
- `elf:j<n>` night ionization
- `elf:n<val>` PM normal threshold
- `elf:s<val>` PM strong threshold
- `elf:P` / `elf:p` PM preview on/off
- `elf:t[0|1]` anti-smog shield

## 5) Live command verification done on device

Observed in `/var/log/wm_pth.log`:
- sending `spd:b1` produced `gc_new_values, ret val frame:['V', 3, 1]`
- sending `nag:T21` produced `gc_new_values, ret val frame:['V', 15, 21]`
- sending `bps:ta,gwc:ta,sez:sa` produced `gc_new_values, ret val frame:['V', 9, 2, 10, 2, 12, 2]`

This confirms web command parsing and numeric code mapping are correct.

## 6) Modbus RTU linkage details

Daemon file: `/usr/local/bin/wm-pth-new/modbus.py`
- RTU serial port: `/dev/ttyS2`
- config port: `/dev/ttyS0`
- `holding2cmd` and `coil2cmd` tables map Modbus writes to `CM_SET_*` codes.
- `set_holding()` and `set_coil()` translate Modbus register writes into the same internal queue frames `('MB', ['V', code, value])`.

Implication:
- Web API commands and Modbus register writes converge to the same internal `V` command model.
- HA can safely use web commands for control; behavior should match local panel/app.

## 7) Integration optimization roadmap

1. Add first-class HA entities (not only raw service):
   - `select`: season mode, bypass mode, gwc mode, vent mode
   - `number`: fan gear, heating/cooling setpoint
   - `switch`: boost, humidity control, CO2 control, anti-smog

2. Keep `provent.send_command` as an escape hatch for unsupported commands.

3. Add command validation in HA using known ranges from `mb_ranges`:
   - reject out-of-range values before sending to device.

4. Add optimistic state updates after successful write:
   - patch coordinator cache with expected value and refresh shortly after.

5. Add optional debug logger in integration:
   - log outgoing command + response + pre/post snapshot (selected keys only).

## 8) Open questions for deeper future work

- Decode `elf` payload fully (currently exposed as raw string).
- Confirm exact semantics of all `spd` flags and `stn` states.
- Capture physical RS485 RTU traffic (`/dev/ttyS2`) for byte-level protocol docs (optional if internal code remains accessible).
