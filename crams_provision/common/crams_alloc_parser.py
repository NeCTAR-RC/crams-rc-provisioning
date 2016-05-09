from crams_provision.common.nectar_allocation import NcProject, NcNovaQuota, \
    NcCinderQuota, NcSwiftQuota

RAM_PER_CORE = 4096


def parse_allocations(alloctions):
    alloc_list = []

    for alloc in alloctions:
        pid = alloc.get('id')
        description = alloc.get('title')
        project_ids = alloc.get('project_ids')
        identifier = None
        tenant_uuid = None

        for proj_id in project_ids:

            system = proj_id.get('system')
            system_value = system.get('system')
            p_identifier = proj_id.get('identifier')
            if system_value.lower() == 'nectar':
                identifier = p_identifier
            if system_value.lower() == 'nectar_uuid':
                tenant_uuid = p_identifier
        requests = alloc.get('requests')

        if requests:
            alloc_req = requests[0]
            crams_req_id = alloc_req.get('id')
            expiry = alloc_req.get('end_date')

            # check if it needs to convert project trial
            req_question_resps = alloc_req.get('request_question_responses')
            pt_conversion = False
            allocation_home = None

            for question_resp in req_question_resps:
                question = question_resp.get('question')
                key = question.get('key')
                if key == 'ptconversion':
                    pt_conversion_resp = question_resp.get('question_response')
                    if pt_conversion_resp.lower() == 'true':
                        pt_conversion = True
                if key == 'homenode':
                    allocation_home = question_resp.get('question_response')
                    if allocation_home:
                        allocation_home = allocation_home.lower()

            manage_email = None
            project_contacts = alloc.get('project_contacts')
            for proj_contact in project_contacts:
                contact_role = proj_contact.get('contact_role')
                role_name = contact_role.get('name')
                manage_email = None
                if role_name == 'Applicant':
                    contact = proj_contact.get('contact')
                    manage_email = contact.get('email')

                if not manage_email and role_name == 'Chief Investigator':
                    contact = proj_contact.get('contact')
                    manage_email = contact.get('email')

            nc_project = NcProject(pid, identifier,
                                   description, manage_email,
                                   expiry, pt_conversion,
                                   allocation_home, crams_req_id,
                                   tenant_uuid)
            alloc_list.append(nc_project)

            # parse the compute requests
            compute_requests = alloc_req.get('compute_requests')
            nc_nova_quota_list = []
            if compute_requests:
                for comp_req in compute_requests:
                    comp_req_id = comp_req.get('id')
                    approved_cores = comp_req.get('approved_cores')
                    approved_instances = comp_req.get('approved_instances')
                    comp_prod = comp_req.get('product')
                    prod_id = comp_prod.get('id')
                    ram = approved_cores * RAM_PER_CORE

                    nc_nova_quota = NcNovaQuota(comp_req_id,
                                                approved_cores,
                                                approved_instances,
                                                ram, prod_id)
                    nc_nova_quota_list.append(nc_nova_quota)

            nc_project.set_nova_quota_list(nc_nova_quota_list)

            # parse the storage requests
            storage_requests = alloc_req.get('storage_requests')
            swift_quota_list = []
            cinder_quota_list = []
            if storage_requests:
                for storage_req in storage_requests:
                    req_id = storage_req.get('id')
                    approved_quota = storage_req.get('approved_quota')
                    product = storage_req.get('product')
                    storage_prod_id = product.get('id')
                    storage_type = product.get('storage_type')
                    resource = storage_type.get('storage_type')
                    zone = product.get('zone')
                    zone_name = zone.get('name')
                    if resource.lower() == 'object':
                        o_resource = resource.lower()
                        nc_swift_quota = NcSwiftQuota(req_id,
                                                      o_resource,
                                                      zone_name,
                                                      approved_quota,
                                                      storage_prod_id)
                        swift_quota_list.append(nc_swift_quota)
                    if resource.lower() == 'volume':
                        v_resource = resource.lower()

                        nc_cinder_quota = NcCinderQuota(req_id,
                                                        v_resource,
                                                        zone_name,
                                                        approved_quota,
                                                        storage_prod_id)
                        cinder_quota_list.append(nc_cinder_quota)
            nc_project.set_cinder_quota_list(cinder_quota_list)
            nc_project.set_swift_quota_list(swift_quota_list)

    return alloc_list
