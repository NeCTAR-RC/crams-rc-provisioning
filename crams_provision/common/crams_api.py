import logging

import urllib3
import simplejson

LOG = logging.getLogger(__name__)


def get_approved_requests(url, token):
    http = urllib3.PoolManager()
    headers = {'Authorization': 'Token {}'.format(token)}
    try:
        response = http.request('GET', url=url, headers=headers)
        status = response.status
        if status == 200:
            allocations = simplejson.loads(response.data)
            res = {'success': True, 'allocations': allocations}
        else:
            res = {'success': False, 'reason': status}

    except Exception as e:
        error_msg = 'Failed to connect to the server, {}, error: {}'.format(
            url, e)
        res = {'success': False, 'reason': error_msg}

        LOG.error(error_msg)
    return res


def update_provision_results(url, provision_results_json, token):
    http = urllib3.PoolManager()
    headers = {'Authorization': 'Token {}'.format(token),
               'Content-Type': 'application/json'}

    try:
        response = http.request('POST', url=url, headers=headers,
                                body=provision_results_json)

        status = response.status
        print('Provision updating response status code: {}'.format(status))
        if status == 200 or status == 201:
            res_dict = simplejson.loads(response.data)
            print(res_dict)
            LOG.info('Provision updating callback success')
            print('Provision updating callback success')
        else:
            error_msg = 'Provision updating callback error, ' \
                        '{}'.format(response.data)
            LOG.error(error_msg)
            print(error_msg)
    except Exception as e:
        error_msg = 'Failed to update the provision{}, error: {}'.format(
            url, e)
        print(error_msg)
        LOG.error(error_msg)
