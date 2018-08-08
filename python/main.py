import sys
import io
import contextlib
import json

from flask import make_response


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

    SENTRY_CODE_SNIPPET = request.get_json()['code']
    with SENTRY_STDOUT_FUNCTION() as SENTRY_STDOUT_SOCKET:
        exec(compile(SENTRY_CODE_SNIPPET, 'main.py', 'exec'))
        stdout_list = SENTRY_STDOUT_SOCKET.getvalue().split('\n')
        event_id_item = next(x for x in stdout_list if x.find('SENTRY_EVENT_ID: ') == 0)
        stdout_list.remove(event_id_item)
    res = make_response(json.dumps({'event_id': event_id_item[len('SENTRY_EVENT_ID: ') - 1:], 'logs': '\n'.join(stdout_list)}), 200)
    res.headers["Access-Control-Allow-Origin"] = "*"
    res.headers["Access-Control-Allow-Methods"] = "POST"
    res.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return res
    