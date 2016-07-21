"""
CRAMS NeCTAR Provisioning local settings to override some of default settings

"""

# CRAMS api server
CRAMS_SERVER_BASE = 'http://localhost:8000'
CRAMS_AUTH_API_PATH = 'json_token_auth'
CRAMS_PROVISION_API_PATH = 'api/v1/provision_project/list'
CRAMS_PROVISION_UPDATE_PATH = 'api/v1/provision_project/update'

# --- OPENSTACK Keystone configurations ---
OS_AUTH_URL = 'http://localhost:5000/v3/'
OS_PROJECT_NAME = 'merc_test_project'
OS_USERNAME = 'keystone_admin'
OS_PASSWORD = 'keystone_admin_password'
