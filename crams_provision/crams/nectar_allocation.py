# NeCTAR Project(Tenant)
class NcProject(object):
    def __init__(self, project_id, identifier,
                 description, manager_email,
                 expiry, convert_trial,
                 allocation_home, crams_req_id,
                 tenant_uuid=None, nc_nova_quota_list=None,
                 nc_cinder_quota_list=None, nc_swift_quota_list=None):
        self.project_id = project_id
        self.identifier = identifier
        self.description = description
        self.manager_email = manager_email
        self.expiry = expiry
        self.convert_trial = convert_trial
        self.allocation_home = allocation_home
        self.crams_req_id = crams_req_id
        self.tenant_uuid = tenant_uuid
        self.nc_nova_quota_list = nc_nova_quota_list
        self.nc_cinder_quota_list = nc_cinder_quota_list
        self.nc_swift_quota_list = nc_swift_quota_list

    def set_nova_quota_list(self, nc_nova_quota_list):
        self.nc_nova_quota_list = nc_nova_quota_list

    def set_cinder_quota_list(self, nc_cinder_quota_list):
        self.nc_cinder_quota_list = nc_cinder_quota_list

    def set_swift_quota_list(self, nc_swift_quota_list):
        self.nc_swift_quota_list = nc_swift_quota_list

    def __str__(self):
        return 'crams project id: {}, tenant uuid: {}, ' \
               'tenant name: {}, description: {}, ' \
               'convert trial: {}, allocation_home: {}, expiry: {}, ' \
               'request id: {}, manager email: {}'.format(self.project_id,
                                                          self.tenant_uuid,
                                                          self.identifier,
                                                          self.description,
                                                          self.convert_trial,
                                                          self.allocation_home,
                                                          self.expiry,
                                                          self.crams_req_id,
                                                          self.manager_email)


class NcNovaQuota(object):
    def __init__(self, req_id, cores, instances, ram, product_id):
        self.req_id = req_id
        self.cores = cores
        self.instances = instances
        self.ram = ram
        self.product_id = product_id

    def __str__(self):
        return 'Request id: {}, Cores: {}, ' \
               'RAM: {},  Instances: {}, ' \
               'Product id: {}'.format(self.req_id, self.cores,
                                       self.ram, self.instances,
                                       self.product_id)


class NcCinderQuota(object):
    def __init__(self, req_id, resource, zone, gigabytes, product_id):
        self.req_id = req_id
        self.resource = resource
        self.zone = zone
        self.gigabytes = gigabytes
        self.product_id = product_id

    def __str__(self):
        return 'Request id : {}, Resource: {}, ' \
               'Zone: {}, Gigabytes: {}, ' \
               'Product id: {}'.format(self.req_id, self.resource,
                                       self.zone, self.gigabytes,
                                       self.product_id)


class NcSwiftQuota(NcCinderQuota):
    pass
