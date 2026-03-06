from datetime import timedelta

DOMAIN = "provent"
DEFAULT_NAME = "ProVent RC7 Premium"
CONF_API_PATH = "api_path"
CONF_USE_SSL = "use_ssl"
DEFAULT_API_PATH = "/api"
DEFAULT_PORT = 80
DEFAULT_SSL_PORT = 443
DEFAULT_UPDATE_INTERVAL = timedelta(seconds=20)
PLATFORMS = ["sensor"]
DATA_COORDINATOR = "coordinator"
SERVICE_SEND_COMMAND = "send_command"
ATTR_COMMAND = "command"
ATTR_ENTRY_ID = "entry_id"
