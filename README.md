# decentratelimiter
A decent rate limiter for throttling requests to APIs.

## Running the limiter

To run with gunicorn:

    gunicorn --workers=1 --worker-class=gthread --threads=40 --bind=127.0.0.1:8082 decentratelimiter.limiter:app
