from crams_provision.settings import *

INSTALLED_APPS += (
    'django_nose',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'crams_provision.sqlite3'),
    }
}

# CRAMS api server
CRAMS_SERVER_BASE = 'http://localhost:8080'

CRAMS_AUTH_API_PATH = 'json_token_auth'

CRAMS_PROVISION_API_PATH = 'api/provision_project/list'

CRAMS_PROVISION_UPDATE_PATH = 'api/provision_project/update'

CRAMS_NECTAR_ADMIN = 'nectar'

CRAMS_NECTAR_ADMIN_PASSWORD = 'test'

# --- OPENSTACK Keystone configurations ---
# Using Keystone version 3 api
OS_AUTH_URL = 'https://localhost:5000/v3/'

# Tenant name
OS_TENANT_NAME = 'CRAMS'

# tenant_id
OS_TENANT_ID = 'test'

# admin user name
OS_USERNAME = 'crams'

# admin user id
OS_USER_ID = 'test'

# admin user password
OS_PASSWORD = 'test'

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

NOSE_ARGS = [
    '--with-coverage',
    '--verbosity=2',
    '--cover-xml',  # produle XML coverage info
    '--cover-xml-file=coverage.xml',  # the coverage info file
    '--cover-package=crams_provision,nc_provision',
    '--cover-inclusive',
]
