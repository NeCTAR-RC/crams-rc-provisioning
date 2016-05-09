import unittest.mock as mock
from crams_provision.common.crams_auth import *
from crams_provision.tests.utils import ProvisionTestCase, HttpMockResponse


class CommonMethodsTest(ProvisionTestCase):
    @mock.patch('crams_provision.common.crams_auth.urllib3')
    def test_cram_login(self, urllib3PoolMock):
        url = 'http://dummyUrl'
        user_name = 'dummyUser'
        password = 'dummyPasswd'
        token = 'sdasd34e4fvdsvre54t6'

        # Test Success Response

        def _get_response_common(mock_response_value):
            config = {'PoolManager.return_value.request.'
                      'return_value': mock_response_value}
            urllib3PoolMock.configure_mock(**config)
            return cram_login(url, user_name, password)

        # Test Success value
        login_response = _get_response_common(
            HttpMockResponse.get_success_response({'token': token}))
        self.assertTrue(login_response['success'])
        self.assertEqual(login_response['token'], token)

        # Test Fail value
        login_response = _get_response_common(
            HttpMockResponse.get_bad_request_response())
        self.assertFalse(login_response['success'])
        self.assertEqual(login_response['reason'], 400)

    @mock.patch('crams_provision.common.crams_auth.urllib3')
    def test_cram__kstoken_login(self, urllib3PoolMock):
        url = 'http://dummyUrl'
        ks_token = 'dummyafsad2sddsdfew002fsad1'
        token = 'sdasd34e4fvdsvre54t6'

        def _get_response_common(mock_response_value):
            config = {'PoolManager.return_value.request.'
                      'return_value': mock_response_value}
            urllib3PoolMock.configure_mock(**config)
            return cram__kstoken_login(url, ks_token)

            # Test Success value

        login_response = _get_response_common(
            HttpMockResponse.get_success_response({'token': token}))
        self.assertTrue(login_response['success'])
        self.assertEqual(login_response['token'], token)

        # Test Fail value
        login_response = _get_response_common(
            HttpMockResponse.get_bad_request_response())
        self.assertFalse(login_response['success'])
        self.assertEqual(login_response['reason'], 400)
