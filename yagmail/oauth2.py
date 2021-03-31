"""
Adapted from:
http://blog.macuyiko.com/post/2016/how-to-send-html-mails-with-oauth2-and-gmail-in-python.html

1. Generate and authorize an OAuth2 (generate_oauth2_token)
2. Generate a new access tokens using a refresh token(refresh_token)
3. Generate an OAuth2 string to use for login (access_token)
"""
import os
import base64
import json
import getpass

try:
    from urllib.parse import urlencode, quote, unquote
    from urllib.request import urlopen
except ImportError:
    from urllib import urlencode, quote, unquote, urlopen

try:
    input = raw_input
except NameError:
    pass

GOOGLE_ACCOUNTS_BASE_URL = 'https://accounts.google.com'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'


def command_to_url(command):
    return '%s/%s' % (GOOGLE_ACCOUNTS_BASE_URL, command)


def url_format_params(params):
    param_fragments = []
    for param in sorted(params.items(), key=lambda x: x[0]):
        escaped_url = quote(param[1], safe='~-._')
        param_fragments.append('%s=%s' % (param[0], escaped_url))
    return '&'.join(param_fragments)


def generate_permission_url(client_id):
    params = {}
    params['client_id'] = client_id
    params['redirect_uri'] = REDIRECT_URI
    params['scope'] = 'https://mail.google.com/'
    params['response_type'] = 'code'
    return '%s?%s' % (command_to_url('o/oauth2/auth'), url_format_params(params))


def call_authorize_tokens(client_id, client_secret, authorization_code):
    params = {}
    params['client_id'] = client_id
    params['client_secret'] = client_secret
    params['code'] = authorization_code
    params['redirect_uri'] = REDIRECT_URI
    params['grant_type'] = 'authorization_code'
    request_url = command_to_url('o/oauth2/token')
    encoded_params = urlencode(params).encode('UTF-8')
    response = urlopen(request_url, encoded_params).read().decode('UTF-8')
    return json.loads(response)


def call_refresh_token(client_id, client_secret, refresh_token):
    params = {}
    params['client_id'] = client_id
    params['client_secret'] = client_secret
    params['refresh_token'] = refresh_token
    params['grant_type'] = 'refresh_token'
    request_url = command_to_url('o/oauth2/token')
    encoded_params = urlencode(params).encode('UTF-8')
    response = urlopen(request_url, encoded_params).read().decode('UTF-8')
    return json.loads(response)


def generate_oauth2_string(username, access_token, as_base64=False):
    auth_string = 'user=%s\1auth=Bearer %s\1\1' % (username, access_token)
    if as_base64:
        auth_string = base64.b64encode(auth_string.encode('ascii')).decode('ascii')
    return auth_string


def get_authorization(google_client_id, google_client_secret):
    permission_url = generate_permission_url(google_client_id)
    print('Navigate to the following URL to auth:\n' + permission_url)
    authorization_code = input('Enter verification code: ')
    response = call_authorize_tokens(google_client_id, google_client_secret, authorization_code)
    return response['refresh_token'], response['access_token'], response['expires_in']


def refresh_authorization(google_client_id, google_client_secret, google_refresh_token):
    response = call_refresh_token(google_client_id, google_client_secret, google_refresh_token)
    return response['access_token'], response['expires_in']


def get_oauth_string(user, oauth2_info):
    access_token, expires_in = refresh_authorization(**oauth2_info)
    auth_string = generate_oauth2_string(user, access_token, as_base64=True)
    return auth_string


def get_oauth2_info(oauth2_file):
    oauth2_file = os.path.expanduser(oauth2_file)
    if os.path.isfile(oauth2_file):
        with open(oauth2_file) as f:
            oauth2_info = json.load(f)
    else:
        print("If you do not have an app registered for your email sending purposes, visit:")
        print("https://console.developers.google.com")
        print("and create a new project.\n")
        email_addr = input("Your 'email address': ")
        google_client_id = input("Your 'google_client_id': ")
        google_client_secret = getpass.getpass("Your 'google_client_secret': ")
        google_refresh_token, _, _ = get_authorization(google_client_id, google_client_secret)
        oauth2_info = {
            "email_address": email_addr,
            "google_client_id": google_client_id.strip(),
            "google_client_secret": google_client_secret.strip(),
            "google_refresh_token": google_refresh_token.strip(),
        }
        with open(oauth2_file, "w") as f:
            json.dump(oauth2_info, f)
    return oauth2_info
