import unittest.mock as mock

import nose.tools

from crams_provision.tests.utils import ProvisionTestCase, get_dynamic_class, \
    get_power_set_as_list
from crams_provision import common


# Test _common.py get_keystone_client() works and that settings for
# Keystone User, Passwd etc exists
class CommonMethodsTest(ProvisionTestCase):
    def test_openstack_client(self):
        # Test Keystone
        self.assertIsNotNone(common.get_keystone_client(),
                             'Cannot fetch Keystone client')
        # Test Nova
        self.assertIsNotNone(common.get_nova_client(),
                             'Cannot fetch Nova client')
        # Test Cinder
        self.assertIsNotNone(common.get_cinder_client(),
                             'Cannot fetch Cinder client')
        # Test Swift
        self.assertIsNotNone(common.get_swift_client(),
                             'Cannot fetch Swift client')

    def test_convert_trial_project(self):
        pass  # wait for V3 of Keystone API to be used before writing test

    # Note: cannot autospec the ks_client when using inner attributes
    # like ks_client.roles, ks_client.users etc.
    #  - see http://stackoverflow.com/questions/31709792/
    # patching-a-class-yields-attributeerror-mock-object-
    # has-no-attribute-when-acce
    @mock.patch('crams_provision.common.get_keystone_client')
    def test_add_tenant(self, ks_client):
        kc = ks_client
        name = 'Test Name'
        description = 'Test Description'
        manager_email = 'test@crams.edu.au'
        allocation_id = 2
        expiry = '2016-12-01'
        allocation_home = 'monash'

        # Setup return values for ks_client functions
        # Role find setup
        member_role = get_dynamic_class('Role', {'role': 'Member'})
        manager_role = get_dynamic_class('Role', {'role': 'TenantManager'})

        def role_find_side_effect_fn(name):
            if name == 'Member':
                return member_role
            if name == 'TenantManager':
                return manager_role
            return get_dynamic_class('Role', {'role': name})

        kc.roles.find.side_effect = role_find_side_effect_fn

        # User find setup
        tenant_user = get_dynamic_class('User', {'name': manager_email})

        def users_find_side_effect(name):
            if name == manager_email:
                return tenant_user
            return get_dynamic_class('User', {'name': name})

        kc.users.find.return_value = tenant_user

        # Tenant creation setup
        tenant_id = 'Test001'
        test_tenant = get_dynamic_class('Tenant', {'id': tenant_id})
        # set return value for method
        kc.projects.create.return_value = test_tenant
        kc.domains.find.return_value = "Default"

        # Test normal success scenario
        tenant = common.add_tenant(kc, name,
                                   description, manager_email,
                                   allocation_id, expiry,
                                   allocation_home)
        common.update_tenant(kc, tenant, allocation_id,
                             expiry, allocation_home)

        # start assertions
        kc.projects.create.assert_called_with(domain="Default",
                                              name=name,
                                              description=description,
                                              expires=expiry,
                                              allocation_home=allocation_home,
                                              allocation_id=allocation_id)
        # test create tenant
        kc.projects.update.assert_called_with(tenant_id,
                                              allocation_id=allocation_id,
                                              expires=expiry,
                                              allocation_home=allocation_home)
        # Test update
        kc.roles.grant.assert_has_calls([mock.call(project=tenant,
                                                   user=tenant_user,
                                                   role=manager_role),
                                         mock.call(project=tenant,
                                                   user=tenant_user,
                                                   role=member_role)])

        # Test all AddTenant exceptions
        def add_tenant_exception_fn(exception_class, error_msg_expected):
            with nose.tools.assert_raises(exception_class) as cm:
                common.add_tenant(kc, name, description, manager_email,
                                  allocation_id, expiry, allocation_home)
            self.assertEqual(str(cm.exception), error_msg_expected)

        # Manager not Found, expect a ProvisionException
        kc.users.find.side_effect = Exception('dummy')
        add_tenant_exception_fn(common.ProvisionException,
                                "Couldn't find a unique user with that email")
        kc.users.find.side_effect = None

        # Roles not found
        kc.roles.find.side_effect = Exception('dummy')
        add_tenant_exception_fn(common.ProvisionException,
                                "Couldn't find roles")
        kc.roles.find.side_effect = None

    @mock.patch('crams_provision.common.get_keystone_client')
    def test_update_tenant(self, ks_client):
        kc = ks_client

        tenant_id = 'Test002'
        expected_tenant = get_dynamic_class('Tenant', {'id': tenant_id})
        in_tenant = get_dynamic_class('Tenant', {'id': tenant_id})

        allocation_id = 1
        expiry = '2016-12-12'
        allocation_home = 'monash'

        kc.projects.update.return_value = expected_tenant
        returned_tenant = common.update_tenant(kc, in_tenant,
                                               allocation_id, expiry,
                                               allocation_home)

        self.assertEqual(returned_tenant, expected_tenant)

        # Test all updateTenant exceptions
        # def update_tenant_exception_fn(exception_class, error_msg_expected):
        #    with nose.tools.assert_raises(exception_class) as cm:
        #        update_tenant(kc,testTenant, allocation_id, expiry)
        #    self.assertEqual(str(cm.exception), error_msg_expected)
        # Test tenant not found
        # kc.tenants.update.side_effect = Exception('Tenant not found')
        # update_tenant_exception_fn(Exception, "Tenant not found")
        # returned_tenant = update_tenant(kc,testTenant, allocation_id, expiry)

    @mock.patch('crams_provision.common.nova_client')
    def test_get_nova_quota(self, nova_client):
        nc = nova_client

        # test get_nova_quota
        expected_quota = {'cores': 4, 'ram': 4096, 'instances': 2}
        nc.quotas.get.return_value = expected_quota
        tenant_id = 'Test003'
        tenant = get_dynamic_class('Tenant', {'id': tenant_id})
        returned_quota = common.get_nova_quota(nc, tenant)
        nc.quotas.get.assert_called_with(tenant_id=tenant_id)
        self.assertEqual(returned_quota, expected_quota)

    @mock.patch('crams_provision.common.nova_client')
    def test_add_nova_quota(self, nova_client):
        nc = nova_client
        tenant_id = 'Test004'
        tenant = get_dynamic_class('Tenant', {'id': tenant_id})
        full_quota = {'cores': 4, 'ram': 4096, 'instances': 2}

        # test add_nova_quota all field combinations
        for part_quota_keys in get_power_set_as_list(full_quota.keys()):
            part_quota = {}
            for k in part_quota_keys:
                part_quota[k] = full_quota[k]

            # print(partQuota)
            cores = part_quota.get('cores', None)
            instances = part_quota.get('instances', None)
            ram = part_quota.get('ram', None)

            nc.quotas.update.return_value = part_quota
            returned_quota = common.add_nova_quota(nc, tenant, cores,
                                                   instances, ram)
            nc.quotas.update.assert_called_with(tenant_id=tenant_id,
                                                **part_quota)
            self.assertEqual(returned_quota, part_quota)
