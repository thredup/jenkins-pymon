#!/usr/local/bin/python
"""Thios is Jenkins HTTP check remote modue."""
import sys
import os
from datetime import datetime
import requests
from datadog import initialize
from datadog import api
import yaml


metrics_token = os.environ['JENKINS_METRICS_TOKEN']
jenkins_uri = ("https://{0}").format(os.environ['JENKINS_HOST'])
api_key = os.environ('DATADOG_API_KEY')
app_key = os.environ('DATADOG_APP_KEY')


options = {
    'api_key': api_key,
    'app_key': app_key
}

initialize(**options)
metrics_url = ("{0}/metrics/{1}/metrics").format(jenkins_uri, metrics_token)
ping_url = ("{0}/metrics/{1}/ping").format(jenkins_uri, metrics_token)
healthcheck_url = ("{0}/metrics/{1}/healthcheck").format(jenkins_uri, metrics_token) # noqa

# Parse config file
with open("cfg/config.yaml", 'r') as stream:
    try:
        config = yaml.load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        sys.exit(1)

cfg_metrics = config['metrics']

# populate mentrics tags
tags = []
if 'tags' in config:
    for tag in config['tags']:
        tags.append(("{0}:{1}").format(tag['name'], tag['value']))


def host_ping():
    """Ping Jenkins and report its alive."""
    ping_tag = tags
    ping_tag.append("type:healthchek")
    try:
        request = requests.get(ping_url)
        pingcheck = request.content.rstrip()
    except requests.exceptions.RequestException as e:
        api.Metric.send(
            metric='jenkins.healthcheck.ping',
            host=config['host'],
            points=1,
            tags=ping_tag,
            type='gauge'
        )
        print(("Jenkins communication error {0}").format(datetime.utcnow().isoformat(), e)) # noqa
        sys.exit(1)
    if request.ok and pingcheck == 'pong':
        api.Metric.send(
            metric='jenkins.healthcheck.ping',
            host=config['host'],
            points=1,
            tags=ping_tag,
            type='gauge'
        )
        print(("{0} Jenkins ping").format(datetime.utcnow().isoformat()))


def report_healthcheck():
    """Send Healthcheck."""
    # Request metrics data from Jenkins server
    health_tag = tags
    health_tag.append("type:healthchek")
    try:
        request = requests.get(healthcheck_url)
        healthcheck = request.json()
    except requests.exceptions.RequestException as e:
        print(("Jenkins communication error {0}").format(datetime.utcnow().isoformat(), e)) # noqa
        sys.exit(1)
    # populate mentrics tags
    for check in healthcheck.keys():
        if healthcheck[check]['healthy'] == 'true':
            check_value = 1
        else:
            check_value = 0
        api.Metric.send(
            metric=("jenkins.healthcheck.{0}").format(check),
            host=config['host'],
            points=check_value,
            tags=health_tag,
            type='gauge'
        )
    print(("{0} Jenkins healthcheck").format(datetime.utcnow().isoformat()))


def report_metrics():
    """Report metrics."""
    metrics_tag = tags
    metrics_tag.append("type:metrics")
    # Request metrics data from Jenkins server
    try:
        request = requests.get(metrics_url)
        metrics = request.json()
    except requests.exceptions.RequestException as e:
        print(("Jenkins communication error {0}").format(datetime.utcnow().isoformat(), e)) # noqa
        sys.exit(1)

    # Send gauges
    if 'gauges' in cfg_metrics:
        if 'gauges' in metrics:
            for gauge in cfg_metrics['gauges']:
                api.Metric.send(
                    metric=gauge,
                    host=config['host'],
                    points=metrics['gauges'][gauge]['value'],
                    tags=metrics_tag,
                    type='gauge'
                )
        print(("{0} Jenkins gauges").format(datetime.utcnow().isoformat()))

    # Send meters
    if 'meters' in cfg_metrics:
        if 'meters' in metrics:
            for meter in cfg_metrics['meters']:
                api.Metric.send(
                    metric=meter,
                    host=config['host'],
                    points=metrics['meters'][meter]['count'],
                    tags=metrics_tag,
                    type='counter'
                )
        print(("{0} Jenkins meters").format(datetime.utcnow().isoformat()))


host_ping()
report_healthcheck()
report_metrics()
