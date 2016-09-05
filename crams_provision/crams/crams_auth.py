import logging

import urllib3
import simplejson

LOG = logging.getLogger(__name__)


def cram_login(url, username, password):
    http = urllib3.PoolManager()
    json_body = simplejson.dumps({'username': username, 'password': password})
    headers = {'Content-Type': 'application/json'}
    try:
        response = http.request('POST', url=url, headers=headers,
                                body=json_body)
        status = response.status
        if status == 200:
            res_dict = simplejson.loads(response.data)
            token = res_dict.get('token')
            auth_response = {'success': True, 'token': token}
        else:
            auth_response = {'success': False, 'reason': status}
    except Exception as e:
        error_msg = 'Failed to connect to the server, {}, error: {}'.format(
            url, e)
        auth_response = {'success': False, 'reason': error_msg}

        LOG.error(error_msg)
    return auth_response


def cram_kstoken_login(url, ks_token):
    http = urllib3.PoolManager()
    json_body = simplejson.dumps({'token': ks_token})
    headers = {'Content-Type': 'application/json'}
    try:
        response = http.request('POST', url=url, headers=headers,
                                body=json_body)
        status = response.status
        LOG.debug('crams keystone token login status code: '
                  '{}'.format(status))
        if status == 200:
            res_dict = simplejson.loads(response.data)
            token = res_dict.get('token')
            auth_response = {'success': True, 'token': token}
        else:
            auth_response = {'success': False, 'reason': status}
    except Exception as e:
        error_msg = 'Failed to connect to the server, {}, error: {}'.format(
            url, e)
        auth_response = {'success': False, 'reason': error_msg}

        LOG.error(error_msg)
    return auth_response
