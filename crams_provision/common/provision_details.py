class System(object):
    def __init__(self, id, system):
        self.id = id
        self.system = system

    def __str__(self):
        return 'id: {}, system: {}'.format(self.id, self.system)

    def to_dict(self):
        system_dict = dict()
        system_dict['id'] = self.id
        system_dict['system'] = self.system
        return system_dict


class ProjectId(object):
    def __init__(self, identifier, system):
        self.identifier = identifier
        self.system = system

    def __str__(self):
        return 'Identifier: {}  system: {}'.format(self.identifier,
                                                   self.system)

    def to_dict(self):
        proj_id_dict = dict()
        proj_id_dict['identifier'] = self.identifier
        proj_id_dict['system'] = self.system.to_dict()
        return proj_id_dict


class Prod(object):
    def __init__(self, id):
        self.id = id

    def __str__(self):
        return 'id: {}'.format(self.id)


class ComputeProvisionStatus(object):
    def __init__(self, id, is_success=False, message=None, compute_prod=None):
        self.id = id
        self.is_success = is_success
        self.message = message
        self.compute_prod = compute_prod

    def __str__(self):
        return '{}, {}, {}, product {}'.format(self.id,
                                               self.is_success,
                                               self.message,
                                               self.compute_prod)

    def to_dict(self):
        comp_dict = dict()
        comp_dict['id'] = self.id
        comp_dict['message'] = self.message
        comp_dict['success'] = self.is_success
        comp_dict['compute_product'] = {'id': self.compute_prod.id}
        return comp_dict


class StorageProvisionStatus(object):
    def __init__(self, id, is_success=False, message=None, storage_prod=None):
        self.id = id
        self.is_success = is_success
        self.message = message
        self.storage_prod = storage_prod

    def __str__(self):
        return '{}, {}, {}, product {}'.format(self.id,
                                               self.is_success,
                                               self.message,
                                               self.storage_prod)

    def to_dict(self):
        st_dict = dict()
        st_dict['id'] = self.id
        st_dict['message'] = self.message
        st_dict['success'] = self.is_success
        st_dict['storage_product'] = {'id': self.storage_prod.id}
        return st_dict


class RequestProvisionStatus(object):
    def __init__(self, id, compute_provisions=None, storage_provisions=None):
        self.id = id
        self.compute_provisions = compute_provisions
        self.storage_provisions = storage_provisions

    def __str__(self):
        return 'id: {}'.format(self.id)


class ProjectProvisionStatus(object):
    def __init__(self, id, is_success=False, message=None, project_ids=None,
                 request_provisions=None):
        self.id = id
        self.is_success = is_success
        self.message = message
        self.project_ids = project_ids
        self.request_provisions = request_provisions

    def _print_details(self):
        print(self.__str__())

        if self.request_provisions:
            for req_provision in self.request_provisions:

                print('request: {}'.format(req_provision))

                compute_provisions = req_provision.compute_provisions
                for compute_provision in compute_provisions:
                    print('    {}'.format(compute_provision))

                storage_provisions = req_provision.storage_provisions
                for storage_provision in storage_provisions:
                    print('    {}'.format(storage_provision))

        if self.project_ids:
            for project_id in self.project_ids:
                print('{}'.format(project_id))

    def to_dict(self):
        alloc_resp_dict = dict()
        alloc_resp_dict['id'] = self.id
        alloc_resp_dict['message'] = self.message
        alloc_resp_dict['success'] = self.is_success
        alloc_resp_dict['requests'] = []
        if self.request_provisions:
            request_provision_list = []
            alloc_resp_dict['requests'] = request_provision_list
            for request_prov in self.request_provisions:
                request_prov_dict = dict()
                request_provision_list.append(request_prov_dict)

                request_prov_dict['id'] = request_prov.id
                storage_provisions = request_prov.storage_provisions
                request_prov_dict['storage_requests'] = []
                if storage_provisions:
                    storage_prov_list = []
                    request_prov_dict['storage_requests'] = storage_prov_list
                    for storage_prov in storage_provisions:
                        storage_prov_list.append(storage_prov.to_dict())

                compute_provisions = request_prov.compute_provisions
                request_prov_dict['compute_requests'] = []
                if compute_provisions:
                    compute_prov_list = []
                    request_prov_dict['compute_requests'] = compute_prov_list
                    for compute_prov in compute_provisions:
                        compute_prov_list.append(compute_prov.to_dict())
        project_id_list = []
        alloc_resp_dict['project_ids'] = project_id_list
        if self.project_ids:
            for project_id in self.project_ids:
                project_id_list.append(project_id.to_dict())
        return alloc_resp_dict

    def __str__(self):
        return 'id: {}, is success: {}, message: {}'.format(self.id,
                                                            self.is_success,
                                                            self.message)
