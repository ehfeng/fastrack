import sys
import io
import contextlib
import json
import re

from flask import make_response
import requests

@contextlib.contextmanager
def SENTRY_STDOUT_FUNCTION(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = io.StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old


def run(request):
    if request.method == 'OPTIONS':
        res = make_response()
        res.headers["Access-Control-Allow-Origin"] = "*"
        res.headers["Access-Control-Allow-Methods"] = "POST"
        res.headers["Access-Control-Allow-Headers"] = "Content-Type"
        res.status_code = 204
        return res

    assert request.get_json().get('code'), 'request body must have code'
    assert request.get_json().get('slug') or request.get_json().get('email')

    slug = request.get_json().get('slug')
    SENTRY_CODE_SNIPPET = request.get_json()['code']

    if not slug:
        res = requests.get("https://fastrack.ngrok.io/createuser/?email={}&platform=python".format(request.get_json()['email']))
        assert res.json()['public_key']
        assert res.json()['secret_key']
        slug = res.json()['organization_slug']

        key_re = re.compile('\<key\>')
        secret_re = re.compile('\<secret\>')
        SENTRY_CODE_SNIPPET = key_re.sub(res.json()['public_key'], SENTRY_CODE_SNIPPET)
        SENTRY_CODE_SNIPPET = secret_re.sub(res.json()['secret_key'], SENTRY_CODE_SNIPPET)

    
    with SENTRY_STDOUT_FUNCTION() as SENTRY_STDOUT_SOCKET:
        exec(compile(SENTRY_CODE_SNIPPET, 'main.py', 'exec'))
        stdout_list = SENTRY_STDOUT_SOCKET.getvalue().split('\n')
        event_id_item = next(x for x in stdout_list if x.find('SENTRY_EVENT_ID: ') == 0)
        stdout_list.remove(event_id_item)
    event_id = event_id_item[len('SENTRY_EVENT_ID: ') - 1:]

    res = make_response(json.dumps({'slug': slug, 'event_id': event_id, 'logs': '\n'.join(stdout_list)}), 200)
    res.headers["Access-Control-Allow-Origin"] = "*"
    res.headers["Access-Control-Allow-Methods"] = "POST"
    res.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return res
