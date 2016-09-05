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


def main(argv=None):
    parser = argparse.ArgumentParser(add_help=True,
                                     prog='crams-provision-nectar',
                                     description='''
                                     By default provisions all pending
                                     allocation requests
                                     '''
                                     )

    group = parser.add_mutually_exclusive_group()

    group.add_argument('-l', '--list', action="store_true",
                       help='list all allocations ids and exit')

    group.add_argument('-r', '--request-id', action='store',
                       dest='request_id', type=int,
                       help='only provision the specified allocation '
                       'request id')

    parser.add_argument('-d', '--debug', action="store_true",
                        help='enable debug logging')

    args = parser.parse_args()
    if args.debug:
        settings.LOGGING_CONF['handlers']['console']['level'] = 'DEBUG'
        settings.LOGGING_CONF['root']['level'] = 'DEBUG'
        settings.LOGGING_CONF['loggers']['crams_provision']['level'] = 'DEBUG'

    logging.config.dictConfig(settings.LOGGING_CONF)

    list_command = args.list
    req_id = args.request_id

    # will rise error if request id is 0 or negative number
    if req_id and req_id < 1:
        parser.error('the allocation id must be greater than 0')

    # if no -l and no -p arguments, process all allocations provisioning
    if not list_command and not req_id:
        allocations_provision()
        sys.exit(0)

    # list all allocation request and exit
    if list_command:
        list_allocation_ids()
        sys.exit(0)

    # provision single allocation request
    if req_id:
        single_req_provision(req_id)
        sys.exit(0)


if __name__ == "__main__":
    main()
