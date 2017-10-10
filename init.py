"""Thios is Jenkins HTTP check remote modue."""
import sys
import os
import requests
from datadog import initialize
from datadog import api
import yaml


metrics_token = os.environ['JENKINS_METRICS_YOKEN']
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
healthcheck_url = ("{0}/metrics/{1}healthcheck").format(jenkins_uri, metrics_token) # noqa

# Parse config file
with open("config.yaml", 'r') as stream:
    try:
        config = yaml.load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        sys.exit(1)

cfg_metrics = config['metrics']

# Request metrics data from Jenkins server
try:
    request = requests.get(metrics_url)
    metrics = request.json()
except requests.exceptions.RequestException as e:
    print e
    sys.exit(1)

# populate mentrics tags
tags = []
if 'tags' in config:
    for tag in config['tags']:
        tags.append(("{0}:{1}").format(tag['name'], tag['value']))

# Send gauges
if 'gauges' in cfg_metrics:
    if 'gauges' in metrics:
        for gauge in cfg_metrics['gauges']:
            api.Metric.send(
                metric=gauge,
                host=config['host'],
                points=metrics['gauges'][gauge]['value'],
                tags=tags,
                type='gauge'
            )

# Send meters
if 'meters' in cfg_metrics:
    if 'meters' in metrics:
        for meter in cfg_metrics['meters']:
            api.Metric.send(
                metric=meter,
                host=config['host'],
                points=metrics['meters'][meter]['count'],
                tags=tags,
                type='counter'
            )
