from collections import namedtuple
from functools import partial
import json
import urllib
from urllib.parse import urlunsplit
import requests


UrlTuple = namedtuple('UrlTuple', ['scheme', 'netloc', 'path', 'query', 'fragment'])

# TODO: Web API calls need to throw exceptions
JARVIS_API_URI = "localhost:3000"


def get_jarvis_resource(endpoint, resource_id):
    r = requests.get("http://{0}/{1}/{2}".format(JARVIS_API_URI, endpoint,
        urllib.parse.quote(resource_id)))

    if r.status_code == 200:
        return r.json()
    elif r.status_code == 404:
        print("Jarvis-api not found: {0}".format(resource_id))
    else:
        print("Jarvis-api error: {0}, {1}".format(r.status_code, r.json()))

get_log_entry = partial(get_jarvis_resource, 'logentries')
get_tag = partial(get_jarvis_resource, 'tags')


def put_jarvis_resource(endpoint, resource_id, resource_updated):
    r = requests.put("http://{0}/{1}/{2}".format(JARVIS_API_URI, endpoint,
        urllib.parse.quote(resource_id)),
            json=resource_updated)

    if r.status_code == 200:
        return r.json()
    elif r.status_code == 400:
        print("Jarvis-api bad request: {0}".format(r.json()))
        print(json.dumps(resource_updated))
    elif r.status_code == 404:
        print("Jarvis-api not found: {0}".format(resource_id))


def post_jarvis_resource(endpoint, resource_request):
    r = requests.post("http://{0}/{1}".format(JARVIS_API_URI, endpoint),
            json=resource_request)

    if r.status_code == 200:
        return r.json()
    else:
        print("Jarvis-api error: {0}, {1}".format(r.status_code, r.json()))


def query(endpoint, query_params):
    def query_jarvis_resources(url):
        """
        Recursively query for all tags
        """
        r = requests.get(url)

        if r.status_code == 200:
            result = r.json()

            # Try to pull out next link
            links = [link['href'] for link in result['links']
                    if link['rel'] == "next"]
            next_link = links.pop() if links else None

            more_items = query_jarvis_resources(next_link) \
                if next_link else []
            return result['items'] + more_items
        else:
            print("Jarvis-api error: {0}".format(r.status_code))
            return []

    def query_param(field, value):
        return "{0}={1}".format(field, urllib.parse.quote(value)) \
                if value else ""

    query = "&".join([query_param(field, value)
        for field, value in query_params])
    url = urlunsplit(UrlTuple("http", JARVIS_API_URI, endpoint, query, ""))

    return query_jarvis_resources(url)

