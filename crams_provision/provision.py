import argparse
import logging.config
import sys

from crams_provision import settings
from crams_provision.rcprovision import NcProvision

LOG = logging.getLogger(__name__)


def list_allocation_ids():
    """
    List allocation request ids
    :return:
    """
    rc_provision = NcProvision()
    all_alloc_list, token = rc_provision.fetch_alloc()
    req_ids = []
    for allo in all_alloc_list:
        req_ids.append(allo.crams_req_id)
    print(req_ids)


def single_req_provision(request_id):
    """
    Single allocation request provision
    :param request_id:
    :return:
    """
    rc_provision = NcProvision()
    all_alloc_list, token = rc_provision.fetch_alloc()
    found_allo = None
    for alloc in all_alloc_list:
        req_id = alloc.crams_req_id
        if request_id == req_id:
            found_allo = alloc
    if found_allo:
        alloc_list = [found_allo]
        rc_provision.provision(alloc_list, token)
    else:
        print('request not found for id: {}'.format(request_id))


def allocations_provision():
    """
    All allocation provision
    :return:
    """
    rc_provision = NcProvision()
    all_alloc_list, token = rc_provision.fetch_alloc()
    rc_provision.provision(all_alloc_list, token)


def provision_usage():
    return '''
        crams-provision-nectar [-h] [-l | -p [request_id]] [-d]

        optional arguments:

        -l, --list                                   list all allocations ids
                                                     and exit

        -p [request_id], --provision [request_id]    provision all allocations
                                                     or provision a single
                                                     allocation request id
                                                     and exit

        -d, --debug                                  run provisioning in debug
                                                     mode

        -h, --help                                   show the help message
                                                     and exit
    '''


def main(argv=None):
    parser = argparse.ArgumentParser(usage=provision_usage(), add_help=False)
    group = parser.add_mutually_exclusive_group()

    group.add_argument('-l', '--list', action="store_true",
                       help='list all allocations ids and exit')

    group.add_argument('-p', '--provision', action='store', default=-1,
                       dest='request_id', nargs='?', type=int,
                       help='provisioning allocations')

    parser.add_argument('-d', '--debug', action="store_true",
                        help='run provisioning in debug mode')

    parser.add_argument('-h', '--help', action="store_true",
                        help='show the help message and exit')

    args = parser.parse_args()
    if args.debug:
        settings.LOGGING_CONF['handlers']['console']['level'] = 'DEBUG'
        settings.LOGGING_CONF['root']['level'] = 'DEBUG'
        settings.LOGGING_CONF['loggers']['crams_provision']['level'] = 'DEBUG'

    logging.config.dictConfig(settings.LOGGING_CONF)
    LOG.debug('running provision ...')
    if args.help:
        print(provision_usage())
        sys.exit(2)

    if args.list:
        list_allocation_ids()
        sys.exit(2)
    else:
        req_id = args.request_id
        if (not req_id and req_id == 0) or (req_id and req_id < 0):
            parser.error('the allocation id must be greater than 0')

        if req_id and req_id > 0:
            LOG.info('starting to provision a single allocation: {}'.format(
                req_id))
            single_req_provision(req_id)
        else:
            LOG.info('starting to provision all allocations')
            allocations_provision()
        sys.exit(2)


if __name__ == "__main__":
    main()
