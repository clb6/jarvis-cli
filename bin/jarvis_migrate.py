#! python

import sys, time
import pprint
import requests
from jarvis_cli import client

DBCONN_PREV = client.DBConn("localhost", "3000")
DBCONN_NEXT = client.DBConn("localhost", "3001")


def migrate_resources(resource_type, transform_func, post_to_new_func):

    to_migrate = [ transform_func(r)
            for r in client.query(resource_type, DBCONN_PREV, []) ]

    print("Migrate #{0}: {1}".format(resource_type, len(to_migrate)))

    def migrate_reverse_result(r_prev):
        return None if post_to_new_func(r_prev) else r_prev

    start_time = time.time()
    results = [ migrate_reverse_result(r_prev) for r_prev in to_migrate ]

    num_attempted = len(to_migrate)
    num_succeeded = len(list(filter(lambda x: not x, results)))
    print("#attempted: {0}, #succeeded: {1}, elapsed: {2}s".format(
        num_attempted, num_succeeded, time.time()-start_time))


if "__main__" == __name__:
    resource_type = sys.argv[1]

    if "tag" in resource_type:

        def transform(tag):
            """Transform to tag request"""
            del tag['version']
            return tag

        # NOTE!
        # 1. Errors regardless of whether 400 or 409 are treated equally.
        # 2. The method "migrate_tags" was written before the "skip_tags_check"
        # came out. Originally thought tags could be migrated without it but then
        # realized that there are circular relationships

        def post_to_new(tag_prev):
            return client.post_tag(DBCONN_NEXT, tag_prev, skip_tags_check=True)

        migrate_resources("tags", transform, post_to_new)

    elif "log" in resource_type:

        def transform(log_entry):
            """Transform to log entry request"""
            del log_entry['version']
            return log_entry

        def post_to_new(log_entry_prev):
            return client.post_log_entry(DBCONN_NEXT, log_entry_prev)

        migrate_resources("logentries", transform, post_to_new)
