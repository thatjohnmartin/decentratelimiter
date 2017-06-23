import time
import threading
import requests
import logging
from functools import wraps
from flask import Flask, request, jsonify

app = Flask("rate_limiter")

logging.basicConfig(
    filename='/var/log/ratelimiter/api.log',
    format='[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
    datefmt='%d/%b/%Y %H:%M:%S',
    level=logging.WARNING
)

log = logging.getLogger(__name__)


def rate_limited(max_per_second):
    lock = threading.Lock()
    min_interval = 1.0 / max_per_second

    def decorate(func):
        last_time_called = time.perf_counter()

        @wraps(func)
        def rate_limited_function(*args, **kwargs):

            green_light = False
            while not green_light:

                with lock:
                    nonlocal last_time_called
                    elapsed = time.perf_counter() - last_time_called
                    left_to_wait = min_interval - elapsed
                    if left_to_wait <= 0:
                        last_time_called = time.perf_counter()
                        green_light = True

                if left_to_wait > 0:
                    time.sleep(left_to_wait)

            return func(*args, **kwargs)

        return rate_limited_function

    return decorate


@rate_limited(20)
def do_thing_api_request(url):
    log.info('Requested thing_api: %s' % url)
    return requests.get(url, timeout=30)


SERVICES = {
    'thing': do_thing_api_request,
}


@app.route('/limit', methods=['POST'])
def limit():
    # example_request = {
    #     'type': 'GET',
    #     'service': 'thing',
    #     'url': 'http://api.foo.com/?a=1&b=4',
    # }

    url = ''
    service = ''

    try:
        request_type = request.json['type']
        service = request.json['service']
        url = request.json['url']

        log.info('Queued %s: %s' % (service, url))

        if request_type == 'GET':
            service_response = SERVICES[service](url)
            wrapped_response = {
                'limit_status': 'ok',
                'status_code': service_response.status_code,
                'text': service_response.text,
            }
        else:
            log.info('Only GET is supported for (%s, %s), returning an error response' % (service, url))
            wrapped_response = {
                'limit_status': 'error',
            }

    except:
        log.warning('Unexpected exception on: (%s, %s)' % (service, url))
        wrapped_response = {
            'limit_status': 'error',
        }

    return jsonify(wrapped_response), 200
