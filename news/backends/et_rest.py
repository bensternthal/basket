import json
import logging
from textwrap import dedent
import time

from django.conf import settings

import requests


log = logging.getLogger(__name__)


class ETError(Exception):
    pass


class ExactTargetREST(object):
    """Client for ExactTarget's "Fuel" RESTful API."""
    _access_token = None
    _access_token_expires = None
    _access_token_expire_buffer = 30  # seconds
    _refresh_token = None
    api_urls = {
        'auth': 'https://auth.exacttargetapis.com/v1/requestToken',
        'sms_send': 'https://www.exacttargetapis.com/sms/v1/messageContact/{msg_id}/send',
        'validate': 'https://www.exacttargetapis.com/address/v1/validateEmail',
    }

    def __init__(self, client_id=None, client_secret=None):
        if client_id is None:
            client_id = getattr(settings, 'ET_CLIENT_ID', None)
            client_secret = getattr(settings, 'ET_CLIENT_SECRET', None)

        if client_id is None:
            raise ValueError('You must provide the Client ID and Client Secret '
                             'from the ExactTarget App Center.')

        self.client_id = client_id
        self.client_secret = client_secret

    def request(self, url_name, data, url_params=None, method='POST', extra_headers=None):
        headers = {'content-type': 'application/json'}

        if url_name != 'auth':
            headers.update(self.auth_header)

        if extra_headers:
            headers.update(extra_headers)

        url = self.api_urls[url_name]
        if url_params:
            url = url.format(**url_params)

        log.debug(dedent('''\
            Sending request...
              * URL: {0} {1}
              * Data: {2!r}
              * Headers: {3!r}''').format(method, url, data, headers))
        resp = requests.request(method, url, data=json.dumps(data), headers=headers)
        log.debug(dedent('''\
            Response received...
              * Status Code: {0.status_code}
              * Response text: {0.text}''').format(resp))
        return resp

    def auth_token_expired(self):
        """Returns boolean true if the access token has expired."""
        return (self._access_token_expires - self._access_token_expire_buffer) < time.time()

    @property
    def auth_header(self):
        return {'Authorization': 'Bearer {0}'.format(self.auth_token)}

    @property
    def auth_token(self):
        if not self._access_token or self.auth_token_expired():
            data = {
                'clientId': self.client_id,
                'clientSecret': self.client_secret,
                'accessType': 'offline',  # so we get a refresh token
            }
            if self._refresh_token:
                data['refreshToken'] = self._refresh_token
            resp = self.request('auth', data)
            resp_data = resp.json()
            if 'errorcode' in resp_data:
                raise ETError('{0}: {1}'.format(resp_data['errorcode'],
                                                resp_data['message']))
            elif 'accessToken' in resp_data:
                self._access_token = resp_data['accessToken']
                self._access_token_expires = time.time() + resp_data['expiresIn']
                self._refresh_token = resp_data['refreshToken']

            else:
                raise ETError('Unknown error during authentication: {0}'.format(resp.text))

        return self._access_token

    def send_sms(self, phone_numbers, message_id):
        if isinstance(phone_numbers, basestring):
            phone_numbers = [phone_numbers]
        data = {
            'mobileNumbers': phone_numbers,
            'Subscribe': False,
        }
        return self.request('sms_send', data, url_params={'msg_id': message_id})

    def validate_email(self, email):
        data = {
            'email': email,
            'validators': ['SyntaxValidator', 'MXValidator', 'ListDetectiveValidator']
        }
        resp = self.request('validate', data)
        return resp.json()['valid']
