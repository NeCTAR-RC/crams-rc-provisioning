import unittest.mock as mock
import copy
from collections import defaultdict

import nose.tools

from nc_provision.ncprovision import NcProvision, ProvisionException
from crams_provision.tests.utils import ProvisionTestCase, get_dynamic_class, \
    get_power_set_as_list
from crams_provision.common.exceptions import IdentifierException


class TenancyTests(ProvisionTestCase):
    def setUp(self):
        self.ncprov_obj = NcProvision()

    @mock.patch('nc_provision._common.get_keystone_client')
    @mock.patch('nc_provision.ncprovision.common')
    def test_tenant_provision(self, _common_mock, kc):
        proj_dict = {}
        proj_dict['identifier'] = 'sad4r4'
        proj_dict['description'] = 'asdfdsafafefefefewwfef45'
        proj_dict['manager_email'] = 'dfdrfre@rgrg.edu'
        proj_dict['crams_req_id'] = 12
        proj_dict['expiry'] = '02-09-2016'
        proj_dict['allocation_home'] = 'monash'
        proj_dict['convert_trial'] = False
        proj_dict['tenant_uuid'] = ''
        nc_project = get_dynamic_class('ProjectData', proj_dict)

        test_tenant = get_dynamic_class('User',
                                        {'name': nc_project.manager_email})

        # Test New tenant creation
        _common_mock.add_tenant.return_value = test_tenant
        # kc = get_dynamic_class('KeystoneMock',
        # {'name':'keystoneClient Mock Object'})
        _common_mock.get_keystone_client.return_value = kc
        self.ncprov_obj._init_clients()
        returned_tenant = self.ncprov_obj.tenant_provision(nc_project)

        _common_mock.add_tenant.assert_called_with(kc,
                                                   nc_project.identifier,
                                                   nc_project.description,
                                                   nc_project.manager_email,
                                                   nc_project.crams_req_id,
                                                   nc_project.expiry,
                                                   nc_project.allocation_home)
        self.assertEqual(returned_tenant, test_tenant)

        # Test update existing tenant
        # config = {'tenants.get.return_value':test_tenant}
        # kc.configure_mock(**config)
        kc.projects.get.return_value = test_tenant
        # add 'tenant_uuid'
        uuid = '4324fdwef343@'
        proj_dict['tenant_uuid'] = uuid
        proj_dict['identifier'] = 'A123456789B123456789C12'
        nc_project = get_dynamic_class('ProjectData', proj_dict)
        returned_tenant = self.ncprov_obj.tenant_provision(nc_project)

        kc.projects.get.assert_called_with(uuid)

        _common_mock.update_tenant.assert_called_with(kc,
                                                      test_tenant,
                                                      nc_project.crams_req_id,
                                                      nc_project.expiry,
                                                      nc_project.
                                                      allocation_home)
        self.assertEqual(returned_tenant, test_tenant)

        # Test convert trial project
        _common_mock.convert_trial_project.return_value = test_tenant
        # add 'convertToTrial'
        proj_dict['convert_trial'] = True
        proj_dict['allocation_home'] = 'monash'
        nc_project = get_dynamic_class('ProjectData', proj_dict)
        returned_tenant = self.ncprov_obj.tenant_provision(nc_project)

        _common_mock.convert_trial_project.assert_called_with(
            nc_project.manager_email,
            nc_project.identifier,
            nc_project.description)

        self.assertEqual(returned_tenant, test_tenant)

        # test ProjId Length <= 64
        def proj_id_length_tenant_exception_fn(exception_class,
                                               error_msg_expected):
            with nose.tools.assert_raises(exception_class) as cm:
                self.ncprov_obj.tenant_provision(nc_project)
            self.assertEqual(str(cm.exception), error_msg_expected)

        nc_project.identifier = '0123456789A123456789B123456789' \
                                'C123456789D123456789E123456789F123456'
        proj_id_length_tenant_exception_fn(IdentifierException,
                                           'Tenant name too long')

    @mock.patch('nc_provision._common.nova_client')
    @mock.patch('nc_provision.ncprovision.common')
    def test_compute_provision(self, _common_mock, nc):
        _common_mock.get_nova_client.return_value = nc
        self.ncprov_obj._init_clients()

        tenant_id = 'Test001_TestTenant'
        tenant = get_dynamic_class('Tenant', {'id': tenant_id})
        full_quota = {'cores': 4, 'ram': 4096, 'instances': 2}
        empty_quota = {'cores': 0, 'ram': 0, 'instances': 0}

        # test add_nova_quota all field combinations
        for part_quota_keys in get_power_set_as_list(full_quota.keys()):
            input_quota = {}
            for k in full_quota.keys():
                input_quota[k] = 0
            for k in part_quota_keys:
                input_quota[k] = full_quota[k]

            def _test_various_ram_allocations(existing_quota, expected_quota):

                existing_quota_obj = get_dynamic_class('ExistingQuota',
                                                       existing_quota)
                _common_mock.get_nova_quota.return_value = existing_quota_obj

                expected_quota_obj = get_dynamic_class('ExpectedQuota',
                                                       expected_quota)
                _common_mock.add_nova_quota.return_value = expected_quota_obj

                returned_quota = self.ncprov_obj.\
                    nova_provision(tenant, get_dynamic_class('InQuota',
                                                             input_quota))
                _common_mock.get_nova_quota.assert_called_with(nc, tenant)
                cores = expected_quota_obj.cores
                instances = expected_quota_obj.instances
                ram = expected_quota_obj.ram
                _common_mock.add_nova_quota.assert_called_with(nc, tenant,
                                                               cores,
                                                               instances, ram)

                print("returned_quota: " + str(returned_quota))
                print("expected_quotaObj: " + str(expected_quota_obj))
                self.assertEqual(returned_quota, expected_quota_obj)

            # Test same as partQuota
            existing_quota = copy.copy(input_quota)
            expected_quota = copy.copy(input_quota)
            _test_various_ram_allocations(existing_quota, expected_quota)

            # Test existing ram > input ram
            existing_quota = copy.copy(input_quota)
            existing_quota['ram'] = input_quota.get('ram', 0) + 5
            expected_quota = copy.copy(input_quota)
            expected_quota['ram'] = existing_quota['ram']
            _test_various_ram_allocations(existing_quota, expected_quota)

        # Test nova_provision exceptions
        def nova_provision_Exception_fn(exception_class, error_msg_expected):
            with nose.tools.assert_raises(exception_class) as cm:
                self.ncprov_obj.nova_provision(tenant, get_dynamic_class(
                    'InQuota', input_quota))
            self.assertEqual(str(cm.exception), error_msg_expected)

        # get existing nova_quota fail, expect a ProvisionException
        exception_msg = 'dummy find'
        _common_mock.get_nova_quota.side_effect = Exception(exception_msg)
        nova_provision_Exception_fn(ProvisionException,
                                    "Nova compute provision error, " +
                                    exception_msg)
        _common_mock.get_nova_quota.side_effect = None
        exception_msg = 'dummy add'
        _common_mock.add_nova_quota.side_effect = Exception(exception_msg)
        _common_mock.get_nova_quota.return_value = get_dynamic_class(
            'ExistingQuota', existing_quota)
        nova_provision_Exception_fn(ProvisionException,
                                    "Nova compute provision error, " +
                                    exception_msg)
        _common_mock.add_nova_quota.side_effect = None

        # test provisionComputeRequests
        expected_quota = full_quota
        compute_request = copy.copy(expected_quota)
        compute_request['req_id'] = 1
        compute_request['product_id'] = 1
        compute_request_obj = get_dynamic_class('InputComputeRequest',
                                                compute_request)
        compute_provisioned_List = []

        existing_quota = copy.copy(empty_quota)
        existing_quotaObj = get_dynamic_class('ExistingQuota', existing_quota)
        _common_mock.get_nova_quota.return_value = existing_quotaObj

        expected_quota_obj = get_dynamic_class('ExpectedQuota', expected_quota)
        _common_mock.add_nova_quota.return_value = expected_quota_obj
        self.ncprov_obj.provision_compute_requests(
            compute_provisioned_List, compute_request_obj, tenant)
        self.assertEqual(len(compute_provisioned_List), 1)
        self.assertTrue(compute_provisioned_List[0].is_success)
        self.assertEqual(compute_provisioned_List[0].message,
                         'Compute resource has been provisioned successfully')

        # Test nova_provision exceptions
        exception_msg = 'dummy'
        _common_mock.get_nova_quota.side_effect = Exception(exception_msg)
        compute_provisioned_List = []
        self.ncprov_obj.provision_compute_requests(
            compute_provisioned_List, compute_request_obj, tenant)
        self.assertFalse(compute_provisioned_List[0].is_success)
        self.assertEqual(compute_provisioned_List[0].message,
                         'Failed to provision compute resource, '
                         'Nova compute provision error, ' + exception_msg)
        _common_mock.get_nova_quota.side_effect = None

    @mock.patch('nc_provision._common.nova_client')
    @mock.patch('nc_provision.ncprovision.common')
    def test_volume_storage_provision(self, _common_mock, nc):
        _common_mock.get_nova_client.return_value = nc
        self.ncprov_obj._init_clients()

        tenant = get_dynamic_class('Tenant', {'id': 'Test001_TestTenant'})
        requesting_nectar_quota = False
        sum_quota = 1000
        storage_provisioned_list = []
        nc_quota = get_dynamic_class('Quota', {'gigabytes': sum_quota,
                                               'product_id': 1,
                                               'req_id': 1,
                                               'resource': 'volume',
                                               'zone': 'melbourne'
                                               })

        # Test provisionCinderRequests
        self.ncprov_obj.provision_cinder_requests(nc_quota,
                                                  requesting_nectar_quota,
                                                  storage_provisioned_list,
                                                  sum_quota, tenant)
        self.assertEqual(len(storage_provisioned_list), 1)
        self.assertTrue(storage_provisioned_list[0].is_success)
        self.assertEquals(storage_provisioned_list[0].message,
                          'melbourne volume 1000 GB has '
                          'been provisioned successfully')

        # Test cinder_volume_provision exceptions
        exception_msg = 'dummy'
        _common_mock.add_cinder_quota.side_effect = Exception(exception_msg)
        storage_provisioned_list = []
        self.ncprov_obj.provision_cinder_requests(nc_quota,
                                                  requesting_nectar_quota,
                                                  storage_provisioned_list,
                                                  sum_quota, tenant)
        self.assertFalse(storage_provisioned_list[0].is_success)
        self.assertEqual(storage_provisioned_list[0].message,
                         'Failed to provision zone - melbourne, volume 1000 '
                         'GB, Cinder volume provision error, ' + exception_msg)
        _common_mock.add_cinder_quota.side_effect = None

    @mock.patch('nc_provision._common.nova_client')
    @mock.patch('nc_provision.ncprovision.common')
    def test_object_storage_provision(self, _common_mock, nc):
        _common_mock.get_nova_client.return_value = nc
        self.ncprov_obj._init_clients()

        tenant = get_dynamic_class('Tenant', {'id': 'Test001_TestTenant'})
        sum_quota = 1000
        storage_provisioned_list = []
        obj_storage = defaultdict(int)
        nc_quota = get_dynamic_class('Quota', {'gigabytes': sum_quota,
                                               'product_id': 1,
                                               'req_id': 1,
                                               'resource': 'object',
                                               'zone': 'nectar'
                                               })

        # Test provisionSwiftRequests
        self.ncprov_obj.provision_swift_request(nc_quota, obj_storage,
                                                storage_provisioned_list,
                                                tenant)
        self.assertEqual(len(storage_provisioned_list), 1)
        self.assertTrue(storage_provisioned_list[0].is_success)
        self.assertEquals(storage_provisioned_list[0].message,
                          'Object 1000 GB has been provisioned successfully')

        # Test cinder_volume_provision exceptions
        exception_msg = 'dummy'
        _common_mock.add_swift_quota.side_effect = Exception(exception_msg)
        storage_provisioned_list = []
        self.ncprov_obj.provision_swift_request(nc_quota, obj_storage,
                                                storage_provisioned_list,
                                                tenant)
        self.assertFalse(storage_provisioned_list[0].is_success)
        self.assertEqual(storage_provisioned_list[0].message,
                         'Failed to provision object - 1000 GB, '
                         'Swift object provision error, ' + exception_msg)
        _common_mock.add_cinder_quota.side_effect = None
