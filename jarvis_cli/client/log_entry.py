# TODO: Yes need to fix this violation of visibility
from functools import partial
from jarvis_cli.client.common import _get_jarvis_resource, _post_jarvis_resource, \
    _put_jarvis_resource, query


def _construct_log_entry_endpoint(event_id):
    return "events/{0}/logentries".format(event_id)

def get_log_entry(event_id, conn, log_entry_id):
    return _get_jarvis_resource(_construct_log_entry_endpoint(event_id), conn,
            log_entry_id)

def post_log_entry(event_id, conn, log_entry_request, quiet=False,
        skip_tags_check=False):
    return _post_jarvis_resource(_construct_log_entry_endpoint(event_id), conn,
            log_entry_request, quiet, skip_tags_check)

def put_log_entry(event_id, conn, log_entry_id, log_entry_request):
    return _put_jarvis_resource(_construct_log_entry_endpoint(event_id), conn,
            log_entry_id, log_entry_request)

query_log_entries = partial(query, "search/logentries")
