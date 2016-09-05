import logging
import sys
from collections import defaultdict

import simplejson

from crams_provision import common
from crams_provision import settings
from crams_provision.crams.crams_alloc_parser import parse_allocations
from crams_provision.crams.crams_api import get_approved_requests
from crams_provision.crams.crams_api import update_provision_results
from crams_provision.crams.crams_auth import cram_kstoken_login
from crams_provision.crams.exceptions import ProvisionException, \
    IdentifierException
from crams_provision.crams.provision_details import ProjectProvisionStatus, \
    RequestProvisionStatus, ComputeProvisionStatus, StorageProvisionStatus, \
    Prod, System, ProjectId

LOG = logging.getLogger(__name__)


class NcProvision(object):
    def __init__(self):
        self.server_base = settings.CRAMS_SERVER_BASE
        self.auth_url = (self.server_base + '/' +
                         settings.CRAMS_AUTH_API_PATH + '/')

        self.cram_provision_url = (self.server_base + '/' +
                                   settings.CRAMS_PROVISION_API_PATH + '/')

        self.provision_update_url = (self.server_base + '/' +
                                     settings.CRAMS_PROVISION_UPDATE_PATH +
                                     '/')

    def _auth(self):
        # return cram_login(self.auth_url, self.auth_admin, self.auth_password)
        return cram_kstoken_login(self.auth_url, self.token)

    def _init_clients(self):
        self.kc = common.get_keystone_client()
        self.nc = common.get_nova_client()
        self.cc = common.get_cinder_client()
        self.sc = common.get_swift_client()
        self.token = common.get_token()

    def parse_cquota(self, cquota):
        zones = {}
        if not cquota:
            return {}
        for resource, quota in sorted([(key, value)
                                       for key, value in cquota._info.items()
                                       if key.split('_', 1)[0]
                                       in ['volumes',
                                           'snapshots',
                                           'gigabytes']]):
            if quota == -1:
                continue
            type = resource.split('_', 1)
            if len(type) > 1:
                resource, zone = type
            else:
                resource = type[0]
                zone = 'nectar'
            if zone not in zones:
                zones[zone] = {resource: quota}
            else:
                zones[zone][resource] = quota
        return zones

    def print_quota(self, title, nquota, cquota, squota):
        quota_string = self.pretty_quota(title, nquota, cquota, squota)
        for line in quota_string:
            print(line)

    def pretty_quota(self, title, nquota, cquota, squota, include_zeros=True):
        quota_string = ["%s:" % title]
        quota_string.append('  Instances: %s' % nquota.instances)
        quota_string.append('  Cores: %s' % nquota.cores)
        quota_string.append('  Ram: %s' % nquota.ram)

        for zone, resources in self.parse_cquota(cquota).items():
            for resource, quota in resources.items():
                if include_zeros or quota > 0:
                    quota_string.append('  %s (%s): %s' % (resource,
                                                           zone, quota))
        if include_zeros or squota > 0:
            quota_string.append('  Object Store Gigabytes: %s' % squota)
        return quota_string

    def fetch_alloc(self):
        try:
            self._init_clients()
        except Exception as ex:
            error_msg = 'Keystone Authorization failed, {}'.format(ex)
            LOG.error(error_msg)
            sys.exit(1)

        crams_auth_response = self._auth()

        if crams_auth_response['success']:
            token = crams_auth_response['token']
            alloc_res = get_approved_requests(self.cram_provision_url, token)
        else:
            error_msg = 'CRAMS Authorization failed, ' \
                        '{}'.format(crams_auth_response['reason'])
            LOG.error(error_msg)
            sys.exit(1)
        alloc_list = []
        if alloc_res['success']:
            allocations = alloc_res['allocations']
            try:
                alloc_list = parse_allocations(allocations)
            except Exception as ex:
                error_msg = 'Failed to parse allocations json, {}'.format(ex)
                LOG.error(error_msg)
                sys.exit(0)
        else:
            error_msg = 'Get allocations failed, {}'.format(
                alloc_res['reason'])
            LOG.error(error_msg)
            sys.exit(0)

        return alloc_list, token

    def provision(self, alloc_list, token):
        LOG.info('Start to provision ...')
        if alloc_list:
            for nc_proj in alloc_list:
                self._print_request_provision(nc_proj)
                tenant = None
                p_id = nc_proj.project_id
                # create a project provision result status
                proj_prov = ProjectProvisionStatus(p_id)

                tenant = self.provison_tenant(nc_proj, proj_prov)

                if tenant:
                    # initialize the request provision results
                    request_provisions = []
                    proj_prov.request_provisions = request_provisions
                    req_prov = RequestProvisionStatus(nc_proj.crams_req_id)
                    request_provisions.append(req_prov)

                    # nova quota
                    nc_nova_quota_list = nc_proj.nc_nova_quota_list
                    if nc_nova_quota_list:
                        # initialize the compute provision results
                        compute_provisions = []
                        req_prov.compute_provisions = compute_provisions

                        for nc_nova_quota in nc_nova_quota_list:
                            # each compute provision result
                            self.provision_compute_requests(
                                compute_provisions,
                                nc_nova_quota, tenant)

                    # cinder volume provision
                    nc_cquota_list = nc_proj.nc_cinder_quota_list
                    requesting_nectar_quota = False
                    sum_quota = 0

                    # initialize storage provision result list
                    storage_provisions = []
                    # add storage provision result list into a request
                    # provision
                    req_prov.storage_provisions = storage_provisions

                    if nc_cquota_list:
                        for nc_cinder_quota in nc_cquota_list:
                            requesting_nectar_quota, sum_quota = \
                                self.provision_cinder_requests(
                                    nc_cinder_quota,
                                    requesting_nectar_quota,
                                    storage_provisions,
                                    sum_quota, tenant)

                    # if none nectar zone selected, just
                    # allocate a volume size in the nectar
                    # zone with a sum size.
                    if not requesting_nectar_quota and sum_quota > 0:
                        try:
                            self.cinder_volume_provision(tenant,
                                                         'nectar',
                                                         sum_quota,
                                                         sum_quota)
                        except Exception as ex:
                            error_msg = '{}'.format(ex)
                            LOG.error(error_msg)

                    # swift object provision
                    obj_storage = defaultdict(int)
                    nc_swift_quota_list = nc_proj.nc_swift_quota_list

                    if nc_swift_quota_list:
                        for nc_swift_quota in nc_swift_quota_list:
                            self.provision_swift_request(
                                nc_swift_quota,
                                obj_storage,
                                storage_provisions,
                                tenant)
                if LOG.isEnabledFor(logging.DEBUG):
                    LOG.debug('start to crams-api callback for provision result ...')
                self.provision_result_callback(proj_prov, token)
        LOG.info('Finished to provision ...')

    def provision_swift_request(self, nc_swift_quota, obj_storage,
                                storage_provisions, tenant):
        resource = nc_swift_quota.resource
        zone = nc_swift_quota.zone
        gigabytes = nc_swift_quota.gigabytes
        obj_storage[(resource, zone)] = gigabytes
        objects = obj_storage[('object', 'nectar')]
        if objects > 0:
            # initialze a object
            # storage provision status
            st_prov = StorageProvisionStatus(
                nc_swift_quota.req_id)
            st_product = Prod(
                nc_swift_quota.product_id)
            st_prov.storage_prod = st_product

            try:
                self.swift_object_provision(tenant,
                                            objects)
                # set object storage provision
                # status and message if success
                st_prov.is_success = True
                st_prov.message \
                    = 'Object {} GB ' \
                      'has been ' \
                      'provisioned ' \
                      'successfully'.format(objects)
            except Exception as ex:
                # set object storage provision error
                # message if failed
                error_msg = 'Failed to provision ' \
                            'object - {} GB, ' \
                            '{}'.format(objects, ex)
                st_prov.message = error_msg
                LOG.error(error_msg)
            storage_provisions.append(st_prov)

    def provision_cinder_requests(self, nc_cinder_quota,
                                  requesting_nectar_quota,
                                  storage_provisions,
                                  sum_quota,
                                  tenant):
        zone = nc_cinder_quota.zone
        gigabytes = nc_cinder_quota.gigabytes
        if zone == 'nectar':
            requesting_nectar_quota = True
        else:
            sum_quota += gigabytes

        # initialize a storage provision result
        st_prov = StorageProvisionStatus(
            nc_cinder_quota.req_id)
        st_product = Prod(nc_cinder_quota.product_id)
        st_prov.storage_prod = st_product
        # allocate the volume size based on the
        # selected zone
        try:
            self.cinder_volume_provision(tenant, zone,
                                         gigabytes,
                                         gigabytes)
            # set the storage provision status
            # and message if success
            st_prov.is_success = True
            st_prov.message = '{} volume {} GB ' \
                              'has been ' \
                              'provisioned ' \
                              'successfully'.format(zone, gigabytes)

        except Exception as ex:
            error_msg = '{}'.format(ex)
            # set storage provision error message
            # if failed
            st_prov.message = 'Failed to ' \
                              'provision zone - {}, ' \
                              'volume {} GB, ' \
                              '{}'.format(zone, gigabytes, error_msg)

            LOG.error(error_msg)
        storage_provisions.append(st_prov)
        return requesting_nectar_quota, sum_quota

    def provision_compute_requests(self, compute_provisions,
                                   nc_nova_quota,
                                   tenant):
        req_id = nc_nova_quota.req_id
        com_prov = ComputeProvisionStatus(req_id)
        com_prod = Prod(nc_nova_quota.product_id)
        com_prov.compute_prod = com_prod
        try:
            self.nova_provision(tenant, nc_nova_quota)
            # set compute provision stauts and message
            # after success
            com_prov.is_success = True
            com_prov.message = 'Compute resource ' \
                               'has been ' \
                               'provisioned ' \
                               'successfully'
        except Exception as ex:
            # set comput provision error message
            # if failed
            error_msg = 'Failed to provision ' \
                        'compute resource, ' \
                        '{}'.format(ex)
            com_prov.message = error_msg
            LOG.error(error_msg)

        # append each compute provision
        # result into list
        compute_provisions.append(com_prov)

    def provison_tenant(self, nc_proj, proj_prov):
        proj_uuid = nc_proj.tenant_uuid
        tenant = None
        try:
            tenant = self.tenant_provision(nc_proj)
            # set the project provision status and message
            # if success
            proj_prov.is_success = True
            proj_prov.message = '{} has been provisoned' \
                                ' successfully'.format(nc_proj.description)

            # set the project uuid
            proj_uuid = tenant.id
            project_ids = self._gen_project_ids(proj_uuid)
            proj_prov.project_ids = project_ids

        except Exception as ex:
            if proj_uuid:
                project_ids = self._gen_project_ids(proj_uuid)
                proj_prov.project_ids = project_ids
            # if project provision failed, just log it and set
            # provision error message
            error_msg = 'Failed to provison project - ' \
                        '{}, {}'.format(nc_proj.description, ex)

            proj_prov.message = error_msg
            LOG.error(error_msg)
        return tenant

    def _gen_project_ids(self, tenant_uuid):
        proj_ids = []
        proj_system = System(4, 'NeCTAR_UUID')
        project_id = ProjectId(tenant_uuid, proj_system)
        proj_ids.append(project_id)
        return proj_ids

    def _print_request_provision(self, nc_project):
        print(nc_project)
        nc_nova_quota_list = nc_project.nc_nova_quota_list
        if nc_nova_quota_list:
            for nc_nova_quota in nc_nova_quota_list:
                print(nc_nova_quota)

        nc_cinder_quota_list = nc_project.nc_cinder_quota_list
        if nc_cinder_quota_list is not None:
            for nc_cinder_quota in nc_cinder_quota_list:
                print(nc_cinder_quota)

        nc_swift_quota_list = nc_project.nc_swift_quota_list
        if nc_swift_quota_list is not None:
            for nc_swift_quota in nc_swift_quota_list:
                print(nc_swift_quota)

    def _print_provisions_details(self, project_provision):
        project_provision._print_details()

    def provision_result_callback(self, project_provision, token):
        provision_result_json = simplejson.dumps(project_provision.to_dict())
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug('provision result: {}'.format(provision_result_json))
        update_provision_results(self.provision_update_url,
                                 provision_result_json, token)

    def tenant_provision(self, nc_project):
        tenant = None
        project_name = nc_project.identifier
        proj_identifier = project_name.strip() \
            .replace(" ", "_") \
            .replace(".", "_") \
            .replace("__", "_")
        if len(proj_identifier) > 32:
            raise IdentifierException('Tenant name too long')

        # checkout if need to convert the trial project
        convert_trial = nc_project.convert_trial
        if convert_trial:
            tenant = common.convert_trial_project(nc_project.manager_email,
                                                  proj_identifier,
                                                  nc_project.description)
            return tenant

        try:
            # if tenant_uuid present. which means it's an updating
            # process.
            tenant_uuid = nc_project.tenant_uuid
            # if tenant_uuid present. which means it's an updating
            # process.
            if tenant_uuid:
                tenant_uuid = nc_project.tenant_uuid
                tenant = self.kc.projects.get(tenant_uuid)
                common.update_tenant(self.kc, tenant,
                                     nc_project.crams_req_id,
                                     nc_project.expiry,
                                     nc_project.allocation_home)
            else:
                tenant = common.add_tenant(self.kc,
                                           proj_identifier,
                                           nc_project.description,
                                           nc_project.manager_email,
                                           nc_project.crams_req_id,
                                           nc_project.expiry,
                                           nc_project.allocation_home)
        except Exception as ex:
            raise ProvisionException('Tenant provision error: {}'.format(ex))

        return tenant

    def nova_provision(self, tenant, nc_nova_quota):
        # add nova quota
        # get current nova quota
        try:
            nquota = common.get_nova_quota(self.nc, tenant)

            cores = nc_nova_quota.cores
            instances = nc_nova_quota.instances
            ram = nc_nova_quota.ram
            # if the tenant has already got more ram,
            # don't reduce it
            if nquota.ram > ram:
                ram = nquota.ram

            nquota = common.add_nova_quota(self.nc, tenant, cores,
                                           instances, ram)
        except Exception as ex:
            raise ProvisionException(
                'Nova compute provision error, {}'.format(ex))
        return nquota

    def cinder_volume_provision(self, tenant, zone, gigabytes, volumes):
        try:
            common.add_cinder_quota(self.cc, tenant, zone, gigabytes, volumes)
        except Exception as ex:
            raise ProvisionException(
                'Cinder volume provision error, {}'.format(ex))

    def swift_object_provision(self, tenant, objects):
        try:
            common.add_swift_quota(self.sc, tenant, objects)
        except Exception as ex:
            raise ProvisionException(
                'Swift object provision error, {}'.format(ex))
