import unittest.mock as mock

from crams_provision.tests.utils import ProvisionTestCase, get_dynamic_class
from crams_provision._common import add_cinder_quota, get_cinder_quota


# test cinder volume storage
class CinderTest(ProvisionTestCase):
    def setUp(self):
        # mock a tenant
        self.tenant = get_dynamic_class('User', {'name': 'test@test.com',
                                                 'email': 'test@test.com',
                                                 'enabled': 'true',
                                                 'id': '1234556',
                                                 'tenantId': '123456',
                                                 'username': 'test@test.com'
                                                 })

    # add a block of volume storage using a mock cinder client
    @mock.patch('crams_provision._common.cinder_client')
    def test_cinder_add_quota(self, cinder_client):
        cc = cinder_client

        # test volume data
        zone = "nectar"  # should be the default zone
        gigabyte = 1000
        volume = 1000

        # mocking quota from results
        quota = get_dynamic_class('Quota', {'tenant_id': self.tenant.tenantId,
                                            'zone': zone,
                                            'gigabyte': gigabyte,
                                            'volume': volume
                                            })

        # mocking "cinder_client.quotas.update" function sets quota
        cinder_client.quotas.update.return_value = quota

        self.assertEquals(
            add_cinder_quota(cc, self.tenant, zone, gigabyte, volume), quota)

    # add a block of volume storage using a mock cinder client with a
    # different zone
    @mock.patch('crams_provision._common.cinder_client')
    def test_cinder_add_quota_zone(self, cinder_client):
        cc = cinder_client

        # test volume data
        zone = "test_zone"  # should be the default zone
        gigabyte = 1000
        volume = 1000

        # mocking quota from results
        quota = get_dynamic_class('Quota', {'tenant_id': self.tenant.tenantId,
                                            'zone': "",
                                            # zone should be empty string
                                            'gigabyte': gigabyte,
                                            'volume': volume
                                            })

        # mocking "cinder_client.quotas.update" function sets quota
        cinder_client.quotas.update.return_value = quota

        self.assertEquals(
            add_cinder_quota(cc, self.tenant, zone, gigabyte, volume), quota)

    # get a storage quota using mock cinder client
    @mock.patch('crams_provision._common.cinder_client')
    def test_cinder_get_quota(self, cinder_client):
        cc = cinder_client

        # mocking quota for results
        quota = get_dynamic_class('Quota', {'tenant_id': self.tenant.tenantId,
                                            'zone': "nectar",
                                            'gigabyte': 1000,
                                            'volume': 1000
                                            })

        # mocking "cinder_client.quotas.get" function
        cinder_client.quotas.get.return_value = quota

        self.assertEquals(get_cinder_quota(cc, self.tenant), quota)
