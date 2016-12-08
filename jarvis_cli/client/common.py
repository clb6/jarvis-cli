from collections import namedtuple
from itertools import chain
from functools import partial
import json
import urllib
import requests


def _build_url(*args):
    """Build string url

    Disappointed in urllib.parse library because it does give the richness to build
    arbitrary URLs"""
    return "/".join(args)


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


def _get_jarvis_resource_unconverted(endpoint, conn, resource_id):
    url = _build_url(conn.url, endpoint, urllib.parse.quote(resource_id))
    r = requests.get(url, auth=(conn.user, conn.password))

    if r.status_code == 200:
        return r.json()
    elif r.status_code == 404:
        print("Jarvis-api not found: {0}".format(resource_id))
    else:
        print("Jarvis-api error: {0}, {1}".format(r.status_code, r.json()))

def _get_jarvis_resource(endpoint, conn, resource_id):
    return _convert(_get_jarvis_resource_unconverted(endpoint, conn, resource_id))

get_tag = partial(_get_jarvis_resource, 'tags')
# WATCH! Events are unconverted.
get_event = partial(_get_jarvis_resource_unconverted, 'events')


def _put_jarvis_resource_unconverted(endpoint, conn, resource_id, resource_updated):
    url = _build_url(conn.url, endpoint, urllib.parse.quote(resource_id))
    r = requests.put(url, auth=(conn.user, conn.password), json=resource_updated)

    if r.status_code == 200:
        return r.json()
    elif r.status_code == 400:
        print("Jarvis-api bad request: {0}".format(r.json()))
        print(json.dumps(resource_updated))
    elif r.status_code == 404:
        print("Jarvis-api not found: {0}".format(resource_id))

def _put_jarvis_resource(endpoint, conn, resource_id, resource_updated):
    return _convert(_put_jarvis_resource_unconverted(endpoint, conn, resource_id,
        resource_updated))

put_tag = partial(_put_jarvis_resource, 'tags')
put_event = partial(_put_jarvis_resource, 'events')


def _post_jarvis_resource_unconverted(endpoint, conn, resource_request, quiet,
        skip_tags_check):
    url = _build_url(conn.url, endpoint)

    if skip_tags_check:
        url = "{0}?skipTagsCheck=true".format(url)

    r = requests.post(url, auth=(conn.user, conn.password), json=resource_request)

    if r.status_code == 200 or r.status_code == 201:
        return r.json()
    else:
        try:
            body = r.json()
        except:
            body = {}

        if not quiet:
            print("Jarvis-api error: {0}, {1}".format(r.status_code, body))

def _post_jarvis_resource(endpoint, conn, resource_request, quiet=False,
        skip_tags_check=False):
    return _convert(_post_jarvis_resource_unconverted(endpoint, conn,
        resource_request, quiet, skip_tags_check))

post_tag = partial(_post_jarvis_resource, 'tags')

def post_event(conn, event_request, quiet=False):
    # FIXME: Events don't use skip_tags..
    return _post_jarvis_resource_unconverted('events', conn, event_request,
            quiet=quiet, skip_tags_check=False)


def query_generator(endpoint, conn, query_params):
    def query_jarvis_resources(url):
        r = requests.get(url, auth=(conn.user, conn.password))

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

    # REVIEW: This whole query url construction needs to be revisited

    next_link = _build_url(conn.url, endpoint)

    def query_param(field, value):
        return "{0}={1}".format(field, urllib.parse.quote(value)) \
                if value else ""

    query_params = list(filter(lambda qp: qp[1] != None, query_params))

    if query_params:
        query = "&".join([query_param(field, value)
            for field, value in query_params])
        next_link = "?".join([next_link, query])

    while True:
        items, next_link = query_jarvis_resources(next_link)
        yield [ _convert(item) for item in items ]

        if not next_link:
            break

    return []

def query(endpoint, conn, query_params):
    return list(chain.from_iterable(
        [ results for results in query_generator(endpoint, conn, query_params) ]))


def get_data_summary(resource_type, conn):
    url = _build_url(conn.url, "datasummary", resource_type)
    r = requests.get(url, auth=(conn.user, conn.password))
    r.raise_for_status()
    return r.json()
