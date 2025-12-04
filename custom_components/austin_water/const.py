from __future__ import annotations

DOMAIN = "austin_water"
DEFAULT_NAME = "Austin Water"
DEFAULT_UPDATE_INTERVAL = 3600  # seconds
DOWNLOAD_URL = "https://austintx.watersmart.com/index.php/Download/hourly?combined=0"
LOGIN_PATH = "https://austintx.watersmart.com/index.php/auth/login"
VERIFY_PATH = "https://austintx.watersmart.com/index.php/auth/verify"
EMAIL_SUBJECT_HINT = "verification"

CONF_EMAIL_HOST = "email_host"
CONF_EMAIL_PORT = "email_port"
CONF_EMAIL_USERNAME = "email_username"
CONF_EMAIL_PASSWORD = "email_password"
CONF_EMAIL_FOLDER = "email_folder"
CONF_WAIT_TIME = "wait_time"
CONF_SUBJECT_FILTER = "subject_filter"

ATTR_USAGE = "usage"
ATTR_LAST_UPDATE = "last_update"
