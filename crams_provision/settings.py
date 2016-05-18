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
# Using Keystone version 3 api
OS_AUTH_URL = 'http://localhost:5000/v3/'

# Tenant name
OS_TENANT_NAME = 'merc_test_project'

# tenant_id
OS_TENANT_ID = '1234124312431234adaf'

# admin user name
OS_USERNAME = 'keystone_admin'

# admin user id
OS_USER_ID = '1234123412341234'

# admin user password
OS_PASSWORD = 'keystone_admin_password'

# Import the local_settings.py to override some of the default settings,
try:
    from crams_provision.local.local_settings import *
except ImportError:
    logging.warning("No local_settings file found.")
