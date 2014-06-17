import time

from django.test import TestCase

from mock import patch, ANY

from news.backends.et_rest import ETError, ExactTargetREST


@patch('news.backends.et_rest.requests.request')
class TestETRESTBackend(TestCase):
    def setUp(self):
        self.api = ExactTargetREST('bunny', 'visiting friends')

    def test_auth_no_add_auth_header(self, mock_req):
        """Auth requests should not contain the auth header."""
        token = 'you see what happens larry'
        mock_req.return_value.json.return_value = {
            'accessToken': token,
            'refreshToken': 'stay outta malibu lebowski',
            'expiresIn': 3000,
        }
        self.assertEqual(self.api.auth_token, token)
        mock_req.assert_called_with('POST', self.api.api_urls['auth'],
                                    data=ANY, headers=ANY)
        self.assertNotIn('Authorization', mock_req.call_args[1]['headers'])

    def test_adds_auth_header(self, mock_req):
        """Non auth requests should contain the auth header."""
        self.api._access_token = 'darkness warshed over The dude.'
        self.api._access_token_expires = time.time() + 60
        self.api.validate_email('dude@example.com')
        mock_req.assert_called_with('POST', self.api.api_urls['validate'],
                                    data=ANY, headers=ANY)
        self.assertEqual(mock_req.call_args[1]['headers']['Authorization'],
                         'Bearer ' + self.api._access_token)

    def test_error_resp_raises(self, mock_req):
        """Error response should raise an exception."""
        mock_req.return_value.json.return_value = {
            'errorcode': 'walter',
            'message': 'you\'re out of your element',
        }
        with self.assertRaises(ETError):
            self.api.validate_email('dude@example.com')
