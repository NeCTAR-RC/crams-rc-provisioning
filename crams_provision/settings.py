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
