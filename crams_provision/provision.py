import sys
import getopt

from crams_provision.rcprovision import NcProvision
import logging.config
from crams_provision import settings


class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

    @classmethod
    def show_help(self):
        usage = ['%s' % '']
        usage.append('%s' % 'usage: provision.py '
                            '[-h | --help] [-l | --list] [id]')
        usage.append('%s' % '')
        usage.append('%s' % '    -h, --help          '
                            'show the help message and exit')
        usage.append('%s' % '    -l, --list          '
                            'list all allocations ids and exit')
        usage.append('%s' % '    id                  '
                            'single allocation request '
                            'provisioning and exit')
        usage.append('%s' % '    provision.py        '
                            'without any arguments. provision all '
                            'allocation requests and exit')
        usage.append('%s' % '')
        for help in usage:
            print(help)


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
    logging.config.dictConfig(settings.LOGGING_CONF)
    try:
        try:
            opts, args = getopt.getopt(sys.argv[1:], "hl", ["help", "list"])
        except getopt.GetoptError as ex:
            raise Usage(ex)
    except Usage as usage:
        print(usage.msg)
        usage.show_help()

        sys.exit(2)

    for opt, o in opts:
        # show help
        if opt == '-h' or opt == '--help':
            Usage.show_help()
            sys.exit(2)
        # list allocation request ids
        if opt == '-l' or opt == '--list':
            list_allocation_ids()
            sys.exit(2)

    # do all alloctions request provisioning
    if len(args) == 0:
        allocations_provision()
        sys.exit(2)
    # single allocation request provisioning
    elif len(args) == 1:
        try:
            id = int(args[0])
            single_req_provision(id)
        except ValueError as ex:
            print('Invalid literal for int: {}'.format(args[0]))
            Usage.show_help()
        sys.exit(2)
    # invalid arguments
    else:
        print('too many arguments')
        Usage.show_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
