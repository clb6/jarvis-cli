import subprocess, os, time, shutil
from datetime import datetime
import jarvis_cli as jc
from jarvis_cli import config, client
from jarvis_cli.client import log_entry as cle


def create_snapshot(environment, config_map):
    snapshot_filepath = "jarvis_snapshot_{0}_{1}.tar.gz".format(environment,
            datetime.utcnow().strftime("%Y%m%d%H%M%S"))
    snapshot_filepath =os.path.join(config.get_jarvis_snapshots_directory(config_map),
            snapshot_filepath)

    data_dir = config.get_jarvis_data_directory(config_map)
    data_top_dirname = os.path.dirname(data_dir)
    data_basename = os.path.basename(data_dir)

    cmd = ["tar", "-czf", snapshot_filepath, "-C", data_top_dirname, data_basename]

    cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    if cp.returncode == 0:
        return snapshot_filepath
    else:
        # Tarballing failed and there maybe a bad tarball so try to remove it
        try:
            os.remove(snapshot_filepath)
        except:
            pass

        print(cp.stdout)


def restore_snapshot(config_map, snapshot_filepath):
    if not os.path.isfile(snapshot_filepath):
        print("Snapshot file does not exist: {0}".format(snapshot_filepath))

    data_dir = config.get_jarvis_data_directory(config_map)
    data_top_dirname = os.path.dirname(data_dir)

    # Move current data directory to a temp
    data_dir_prev = os.path.join(data_top_dirname, "jarvis_prev")
    os.rename(data_dir, data_dir_prev)

    cmd = ["tar", "-xf", snapshot_filepath, "-C", data_top_dirname]
    cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    if cp.returncode == 0:
        if data_dir_prev:
            shutil.rmtree(data_dir_prev)
        return True
    else:
        print(cp.stdout)

        # Something bad happened so go back to previous version
        shutil.rmtree(data_dir)
        os.rename(data_dir_prev, data_dir)
        return False



# TODO: Must test. This code was lifted from jarvis_migrate.py and reworked to be
# library calls.
def _migrate_resources(resource_type, conn_prev, transform_func, post_to_new_func):
    to_migrate = [ transform_func(r)
            for r in client.query(resource_type, conn_prev, []) ]

    print("Migrate #{0}: {1}".format(resource_type, len(to_migrate)))

    def migrate_reverse_result(r):
        return None if post_to_new_func(r) else r

    start_time = time.time()
    results = [ migrate_reverse_result(r) for r in to_migrate ]

    num_attempted = len(to_migrate)
    num_succeeded = len(list(filter(lambda x: not x, results)))
    print("#attempted: {0}, #succeeded: {1}, elapsed: {2}s".format(
        num_attempted, num_succeeded, time.time()-start_time))

def migrate(conn_prev, conn_next):
    def migrate_tags():
        def transform(tag):
            """Transform to tag request"""
            del tag["modified"]
            del tag['version']
            return tag

        # NOTE!
        # 1. Errors regardless of whether 400 or 409 are treated equally.
        # 2. The method "migrate_tags" was written before the "skip_tags_check"
        # came out. Originally thought tags could be migrated without it but then
        # realized that there are circular relationships

        def post_to_new(tag_transformed):
            return client.post_tag(conn_next, tag_transformed, skip_tags_check=True)

        _migrate_resources("tags", conn_prev, transform, post_to_new)

    def migrate_log_entries():
        def transform(log_entry):
            """Transform to log entry request and event request"""
            event = None

            if not log_entry["event"]:
                event = { "created": log_entry["created"],
                        "occurred": log_entry["occurred"],
                        "category": "migrated",
                        "source": jc.EVENT_SOURCE,
                        "weight": 50,
                        "description": log_entry["setting"] }

            del log_entry["modified"]
            del log_entry["version"]
            del log_entry["occurred"]
            del log_entry["setting"]

            return (log_entry, event)

        def post_to_new(decomposed_log_entry):
            log_entry, event = decomposed_log_entry

            event_id = log_entry["event"]
            del log_entry["event"]

            if event:
                event_id = client.post_event(conn_next, event)["eventId"]

            return cle.post_log_entry(event_id, conn_next, log_entry)

        _migrate_resources("logentries", conn_prev, transform, post_to_new)

    def migrate_events():
        def transform(event):
            del event["location"]
            return event

        def post_to_new(event_transformed):
            return client.post_event(conn_next, event_transformed)

        _migrate_resources("events", conn_prev, transform, post_to_new)

    # Order matters in the migration
    migrate_tags()
    migrate_events()
    migrate_log_entries()
