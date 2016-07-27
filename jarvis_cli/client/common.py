from collections import namedtuple
from itertools import chain
from functools import partial
import json
import urllib
from urllib.parse import urlunsplit
import requests


class DBConn(object):
    def __init__(self, host, port):
        self._host = host
        self._port = port

    def connect_uri(self):
        return "{host}:{port}".format(host=self._host, port=self._port)

UrlTuple = namedtuple('UrlTuple', ['scheme', 'netloc', 'path', 'query', 'fragment'])


def _convert(json_object):
    def replace_links(k, v):
        if "Link" in k:
            if isinstance(v, list):
                v = [ link['title'] for link in v ]
            elif v:
                v = v['title']

            return k.replace("Link", ""), v
        else:
            return k, v

    if json_object:
        return dict([ replace_links(k, v) for k,v in json_object.items() ])


def _get_jarvis_resource_unconverted(endpoint, dbconn, resource_id):
    r = requests.get("http://{0}/{1}/{2}".format(dbconn.connect_uri(), endpoint,
        urllib.parse.quote(resource_id)))

    if r.status_code == 200:
        return r.json()
    elif r.status_code == 404:
        print("Jarvis-api not found: {0}".format(resource_id))
    else:
        print("Jarvis-api error: {0}, {1}".format(r.status_code, r.json()))

def _get_jarvis_resource(endpoint, dbconn, resource_id):
    return _convert(_get_jarvis_resource_unconverted(endpoint, dbconn, resource_id))

get_tag = partial(_get_jarvis_resource, 'tags')
# WATCH! Events are unconverted.
get_event = partial(_get_jarvis_resource_unconverted, 'events')


def _put_jarvis_resource_unconverted(endpoint, dbconn, resource_id, resource_updated):
    r = requests.put("http://{0}/{1}/{2}".format(dbconn.connect_uri(), endpoint,
        urllib.parse.quote(resource_id)),
            json=resource_updated)

    if r.status_code == 200:
        return r.json()
    elif r.status_code == 400:
        print("Jarvis-api bad request: {0}".format(r.json()))
        print(json.dumps(resource_updated))
    elif r.status_code == 404:
        print("Jarvis-api not found: {0}".format(resource_id))

def _put_jarvis_resource(endpoint, dbconn, resource_id, resource_updated):
    return _convert(_put_jarvis_resource_unconverted(endpoint, dbconn, resource_id,
        resource_updated))

put_tag = partial(_put_jarvis_resource, 'tags')
put_event = partial(_put_jarvis_resource, 'events')


def _post_jarvis_resource_unconverted(endpoint, dbconn, resource_request, quiet,
        skip_tags_check):
    url = "http://{0}/{1}".format(dbconn.connect_uri(), endpoint)

    if skip_tags_check:
        url = "{0}?skipTagsCheck=true".format(url)

    r = requests.post(url, json=resource_request)

    if r.status_code == 200 or r.status_code == 201:
        return r.json()
    else:
        try:
            body = r.json()
        except:
            body = {}

        if not quiet:
            print("Jarvis-api error: {0}, {1}".format(r.status_code, body))

def _post_jarvis_resource(endpoint, dbconn, resource_request, quiet=False,
        skip_tags_check=False):
    return _convert(_post_jarvis_resource_unconverted(endpoint, dbconn,
        resource_request, quiet, skip_tags_check))

post_tag = partial(_post_jarvis_resource, 'tags')

def post_event(dbconn, event_request, quiet=False):
    # FIXME: Events don't use skip_tags..
    return _post_jarvis_resource_unconverted('events', dbconn, event_request,
            quiet=quiet, skip_tags_check=False)


def query_generator(endpoint, dbconn, query_params):
    def query_jarvis_resources(url):
        r = requests.get(url)

        if r.status_code == 200:
            result = r.json()

            # Try to pull out next link
            links = [link['href'] for link in result['links']
                    if link['rel'] == "next"]
            next_link = links.pop() if links else None

            return result["items"], next_link
        else:
            print("Jarvis-api error: {0}".format(r.status_code))
            return []

    def query_param(field, value):
        return "{0}={1}".format(field, urllib.parse.quote(value)) \
                if value else ""

    query = "&".join([query_param(field, value)
        for field, value in query_params])
    next_link = urlunsplit(UrlTuple("http", dbconn.connect_uri(), endpoint, query, ""))

    while True:
        items, next_link = query_jarvis_resources(next_link)
        yield [ _convert(item) for item in items ]

        if not next_link:
            break

    return []

def query(endpoint, dbconn, query_params):
    return list(chain.from_iterable(
        [ results for results in query_generator(endpoint, dbconn, query_params) ]))


def get_data_summary(resource_type, dbconn):
    url = "http://{0}/datasummary/{1}".format(dbconn.connect_uri(), resource_type)
    r = requests.get(url)
    r.raise_for_status()
    return r.json()
