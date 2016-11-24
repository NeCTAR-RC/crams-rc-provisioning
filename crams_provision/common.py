import time

from keystoneclient.v3 import client as ks_client
from novaclient import client as nova_client
from cinderclient.v2 import client as cinder_client
from swiftclient import client as swift_client
from keystoneauth1 import session
from keystoneclient.auth.identity import v3

from crams_provision import settings
from crams_provision.crams.exceptions import ProvisionException

SWIFT_QUOTA_KEY = 'x-account-meta-quota-bytes'


def add_tenant(kc, name, description, manager_email, allocation_id, expiry,
               allocation_home):
    # get tenant manager user
    try:
        tenant_manager = kc.users.find(name=manager_email)
    except:
        raise ProvisionException("Couldn't find a unique user with that email")

    # get the tenant manager role
    try:
        tenant_manager_role = kc.roles.find(name='TenantManager')
        member_role = kc.roles.find(name='Member')
    except:
        raise ProvisionException("Couldn't find roles")

    # get the default domain, required to create a project in V3
    try:
        domain = kc.domains.get("Default")
    except:
        raise ProvisionException("Couldn't find the default domain")

    # In version 3 of Keystone client the term tenant has been
    # changed to project

    # Create project
    kwargs = {'allocation_id': allocation_id, 'expires': expiry}
    if allocation_home:
        kwargs['allocation_home'] = allocation_home
    project = kc.projects.create(name=name, description=description,
                                 domain=domain, **kwargs)

    # add roles to tenant manager
    kc.roles.grant(user=tenant_manager, role=tenant_manager_role,
                   project=project)
    kc.roles.grant(user=tenant_manager, role=member_role, project=project)

    return project


def update_tenant(kc, tenant, allocation_id, expiry, allocation_home):
    # Link project to allocation
    kwargs = {'allocation_id': allocation_id, 'expires': expiry}
    if allocation_home:
        kwargs['allocation_home'] = allocation_home

    project = kc.projects.update(tenant.id, **kwargs)
    return project


def get_cinder_quota(cc, tenant):
    quota = cc.quotas.get(tenant_id=tenant.id)
    return quota


def add_cinder_quota(cc, tenant, type, gigabytes, volumes):
    if type == 'nectar':
        type = ''
    else:
        type = '_' + type
        # type = ''
    kwargs = {}
    if gigabytes is not None:
        kwargs['gigabytes' + type] = gigabytes
    if volumes is not None:
        # volumes and snapshots are the same as we don't care
        kwargs['volumes' + type] = volumes
        kwargs['snapshots' + type] = volumes

    return cc.quotas.update(tenant_id=tenant.id, **kwargs)


def get_nova_quota(nc, tenant):
    quota = nc.quotas.get(tenant_id=tenant.id)
    return quota


def add_nova_quota(nc, tenant, cores, instances, ram):
    kwargs = {}
    if cores:
        kwargs['cores'] = cores
    if ram:
        kwargs['ram'] = ram
    if instances:
        kwargs['instances'] = instances

    quota = nc.quotas.update(tenant_id=tenant.id, **kwargs)
    return quota


def get_swift_tenant_connection(sc, tenant_id):
    url, token = sc.get_auth()
    base_url = url.split('_')[0] + '_'
    return base_url + tenant_id, token


def get_swift_quota(sc, tenant):
    tenant_url, token = get_swift_tenant_connection(sc, tenant.id)
    swift_account = swift_client.head_account(url=tenant_url, token=token)
    quota = convert_quota_to_gb(int(swift_account.get(SWIFT_QUOTA_KEY, -1)))
    return quota


def convert_quota_to_gb(quota):
    quota_in_gb = quota / 1024 / 1024 / 1024
    return quota_in_gb


def add_swift_quota(sc, tenant, gigabytes):
    tenant_url, token = get_swift_tenant_connection(sc, tenant.id)
    quota_bytes = int(gigabytes) * 1024 * 1024 * 1024
    attempt = 1
    max_attempts = 3
    while attempt <= max_attempts:
        try:
            swift_client.post_account(url=tenant_url,
                                      token=token,
                                      headers={SWIFT_QUOTA_KEY: quota_bytes})
            # return
            break
        except swift_client.ClientException as ex:
            print(ex)
            print("Failed to set swift quota, retying, attempt %s" % attempt)
            time.sleep(attempt * 2)
            attempt += 1
            if attempt == max_attempts:
                raise ProvisionException('Failed to set swift quota, '
                                         '{}'.format(ex))
    # for testing return quota bytes and number of attemps
    return quota_bytes, attempt


def get_keystone_session():
    auth = v3.Password(auth_url=settings.OS_AUTH_URL,
                       username=settings.OS_USERNAME,
                       password=settings.OS_PASSWORD,
                       project_name=settings.OS_PROJECT_NAME,
                       user_domain_id=settings.OS_DOMAIN,
                       project_domain_id=settings.OS_DOMAIN)
    return session.Session(auth=auth)


def get_token():
    return get_keystone_session().get_token()


def get_keystone_client():
    sess = get_keystone_session()
    kc = ks_client.Client(session=sess)
    return kc


def get_nova_client():
    sess = get_keystone_session()
    nc = nova_client.Client(2, session=sess)
    return nc


def get_cinder_client():
    sess = get_keystone_session()
    cc = cinder_client.Client(session=sess)
    return cc


def get_swift_client():
    sc = swift_client.Connection(authurl=settings.OS_AUTH_URL,
                                 user=settings.OS_USERNAME,
                                 key=settings.OS_PASSWORD,
                                 tenant_name=settings.OS_PROJECT_NAME,
                                 auth_version='3')
    return sc


def unlock_all_instances(project_id):
    nc = get_nova_client()
    opts = {"all_tenants": True, 'tenant_id': project_id}
    instances = nc.servers.list(search_opts=opts)
    for i in instances:
        i.unlock()


def convert_trial_project(username, new_project_name, new_description):
    kc = get_keystone_client()
    user = kc.users.find(name=username)
    user_default_project_id = user.default_project_id

    try:
        found_project = kc.projects.find(name=new_project_name)
    except Exception as ex:
        print('project - {} not found'.format(new_project_name))
        found_project = None

    new_alloc_project = None
    if found_project:
        # Project already created,
        # which means the new allocation project is found_project
        new_alloc_project = found_project

    # Get name/desc of existing trial project.
    user_trial_project = kc.projects.get(user_default_project_id)

    # print('----- user default trial project: {}'.format(user_trial_project))

    trial_roles = kc.roles.list(user=user, project=user_trial_project)

    # print('--- trial roles: {}'.format(trial_roles))

    if not new_alloc_project:
        if not user_trial_project.name.startswith('pt-'):
            raise ProvisionException("User's default project is not "
                                     "a pt- project.")
        # get the default domain, required to create a project in V3
        try:
            domain = kc.domains.find(name="Default")
        except:
            raise ProvisionException("Couldn't find the default domain")
            # Create new trial project.

        tmp_project_name = user_trial_project.name + '_copy'
        try:
            new_trial_project = kc.projects.find(name=tmp_project_name)
        except:
            new_trial_project = kc.projects.create(
                name=tmp_project_name,
                description=user_trial_project.description,
                domain=domain)

        # Rename existing trial project to new project name/desc.
        # Reset status in case their pt- is pending suspension.
        new_alloc_project = kc.projects.update(
            user_default_project_id,
            name=new_project_name,
            project_name=new_project_name,
            description=new_description,
            status='')

        # Rename new trial project to match old name.
        kc.projects.update(new_trial_project.id,
                           name=user_trial_project.name,
                           project_name=user_trial_project.name)
        # set the new trial project as user default project
        kc.users.update(user=user, default_project=new_trial_project)

    else:
        new_trial_project = user_trial_project

    # set trial project roles
    if trial_roles:
        for t_role in trial_roles:
            #  remove all trial roles in new alloc_project if exists
            try:
                kc.roles.revoke(user=user,
                                role=t_role,
                                project=new_alloc_project)
            except Exception as ex:
                print('remove trial project roles error: {}'.format(ex))
                pass
            # add trial roles for new trial project
            try:
                kc.roles.grant(user=user,
                               role=t_role,
                               project=new_trial_project)
            except Exception as ex:
                print('add trial project roles error: {}'.format(ex))
                pass

    # add find member role and manager role
    member_role = kc.roles.find(name='Member')
    manager_role = kc.roles.find(name='TenantManager')

    # add member role for user on this new project
    try:
        kc.roles.grant(user=user, role=member_role, project=new_alloc_project)
    except Exception:
        pass
    # add manager role for user on this new project
    try:
        kc.roles.grant(user=user, role=manager_role, project=new_alloc_project)
    except Exception:
        pass

    unlock_all_instances(new_alloc_project.id)

    return new_alloc_project
