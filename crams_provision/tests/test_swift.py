import unittest.mock as mock

from crams_provision.tests.utils import ProvisionTestCase, get_dynamic_class
from crams_provision._common import add_swift_quota, get_swift_quota, \
    get_swift_tenant_connection, convert_quota_to_gb


# test cinder volume storage
class SwiftTest(ProvisionTestCase):
    def setUp(self):
        self.gigabytes = 1000  # gigabyte quota
        self.raw_quota = 1073741824000  # quota in bytes

        # mock a tenant
        self.tenant = get_dynamic_class('User', {'name': 'test@test.com',
                                                 'email': 'test@test.com',
                                                 'enabled': 'true',
                                                 'id': '123456',
                                                 'tenantId': '123456',
                                                 'username': 'test@test.com'
                                                 })

    @mock.patch('crams_provision._common.swift_client')
    def test_swift_add_quota(self, sc):
        sc.get_auth.return_value = \
            ("http://swift-auth-url/" + self.tenant.tenantId, "token_id")

        quota_bytes, conn_attempts = add_swift_quota(sc,
                                                     self.tenant,
                                                     self.gigabytes)

        self.assertEquals(quota_bytes, self.raw_quota)
        self.assertEquals(conn_attempts, 1)

    @mock.patch('crams_provision._common.swift_client')
    def test_swift_get_quota(self, sc):
        sc.get_auth.return_value = \
            ("http://swift-auth-url/" + self.tenant.tenantId, "token_id")

        self.assertIsNotNone(get_swift_quota(sc, self.tenant))

    def test_quota_conversion(self):
        quota_in_gb = convert_quota_to_gb(self.raw_quota)

        self.assertEquals(quota_in_gb, self.gigabytes)

    @mock.patch('crams_provision._common.swift_client')
    def test_swift_tenant_conn(self, sc):
        sc.get_auth.return_value = \
            ("http://swift-auth-url/auth", "token_id")

        url, token = get_swift_tenant_connection(sc, self.tenant.id)

        self.assertEquals(url, "http://swift-auth-url/auth_" + self.tenant.id)
        self.assertEquals(token, "token_id")
