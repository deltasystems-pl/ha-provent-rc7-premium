# ProVent RC7 Premium Home Assistant Integration

This custom component polls `/api/getdata.php` on the ProVent WebManipulator and exposes the parsed JSON values as Home Assistant sensors. It also provides the `provent.send_command` service to emit raw `savedata.php` commands (same format as the official mobile app).

To use it, install the contents of this repository under `custom_components/provent` in your Home Assistant configuration, then configure the integration via UI using the central's IP address and API path (default `/api`).
