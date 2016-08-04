"""
CRAMS NeCTAR Provisioning Settings

"""

import logging

# CRAMS api server
CRAMS_SERVER_BASE = 'http://localhost:8000'
CRAMS_AUTH_API_PATH = 'json_token_auth'
CRAMS_PROVISION_API_PATH = 'api/v1/provision_project/list'
CRAMS_PROVISION_UPDATE_PATH = 'api/v1/provision_project/update'

# --- OPENSTACK Keystone configurations ---
OS_AUTH_URL = 'http://localhost:5000/v3/'
OS_PROJECT_NAME = None
OS_USERNAME = None
OS_PASSWORD = None
OS_DOMAIN = 'default'

# logging directory
PROVISION_LOG_DIR = '/var/log/cramsclient-nectar'

LOGGING_CONF = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        }
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },

        "info_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "simple",
            "filename": PROVISION_LOG_DIR + "/provision.log",
            'maxBytes': 1024 * 1024 * 10,
            "backupCount": 5,
            "encoding": "utf8"
        },

        "error_file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "simple",
            "filename": PROVISION_LOG_DIR + "/provision_errors.log",
            'maxBytes': 1024 * 1024 * 10,
            "backupCount": 5,
            "encoding": "utf8"
        }
    },

    "loggers": {
        "crams_provision": {
            "level": "INFO",
            "handlers": ["console", "info_file_handler", "error_file_handler"],
            "propagate": False
        }
    },

    "root": {
        "level": "INFO",
        "handlers": ["console", "info_file_handler", "error_file_handler"]
    }
}

# Import the local_settings.py to override some of the default settings,
try:
    from crams_provision.local.local_settings import *  # noqa
except ImportError:
    logging.debug("No local_settings file found.")

# Used for production installs
try:
    with open("/etc/cramsclient-nectar/settings.py") as f:
        code = compile(f.read(), "/etc/cramsclient-nectar/settings.py", 'exec')
        exec(code)
except IOError:
    logging.debug("No settings file found at "
                  "/etc/cramsclient-nectar/settings.py.")
