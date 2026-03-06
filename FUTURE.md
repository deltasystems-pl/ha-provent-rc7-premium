# Future Extensions & Exploration

If the current integration works reliably, you can extend it further:

1. **New HA services/entities**
   * Add `number` or `select` entities (fan speed, bypass mode, season mode, GWC state) that send commands like `"spd:b2"`, `"bps:ta"`, `"sez:la"` through the existing `provent.send_command` service.
   * Build dedicated `input_number` or `select` templates that surface `hr`/`bi` values and call the service in automations for manual overrides.
   * Provide a `fan` or `switch` platform for Boost/Wietrzenie by mapping `self.modificationSender` commands (e.g., `"spd:w1"`) to HA toggles.

2. **Digging deeper into the Modbus bridge**
   * SSH into the WebManipulator (IP `192.168.88.98`, user `root`, password `dietpi`) and inspect `/tmp/wm_pipe` or the SQLite `variable` table to see which fields are marked `dir=0` (writes queued to Modbus).
   * Capture Modbus RTU traffic between the daemon and RC7 board to identify register layouts and confirm the JSON wrappers.
   * Log the daemon that reads `/tmp/wm_pipe` to understand how `savedata.php` commands map to Modbus writes; this helps add more precise HA controls or automated diagnostics.

3. **Additional HA exposure**
   * Surface CleanR, electrofilter, and alarm flags as HA `binary_sensor`s or `sensor`s using the decoded `elf` string and modbus registry documentation (`opis-rejestrow-modbus-s6.pdf`).
   * Offer templated sensors that parse `tmp` groups into named airflow temperatures (e.g., `Supply`, `Exhaust`, `Outdoor`, `Bypass`, `Frost`).
   * Record `bps`/`gwc` hex values as percent controls for a bypass slider.

Tell me whenever you want to pursue any of these—especially if you can provide a fresh `savedata` payload from the GUI or a Modbus log—so I can help integrate the commands/services fully.
