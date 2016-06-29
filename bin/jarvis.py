#! python

import os, subprocess, argparse, re
from functools import partial
import webbrowser
from datetime import datetime
from tabulate import tabulate
# REVIEW: dateparser vs dateutil
import dateparser
import jarvis_cli as jc
from jarvis_cli import config, client, admin
from jarvis_cli.client import get_tag, put_tag, post_tag, post_event, query, \
        get_data_summary
from jarvis_cli.client import log_entry as cle


def convert_file_to_json(file_path):
    """
    Form a json representation of a log file.

    Example of return response:

    {
        "author": "John Doe",
        "created": "2015-12-12T16:22:41",
        "occurred": "2015-11-25T00:00:00",
        "version": "0.2.0",
        "tags": ["Weather", "HelloWorld"],
        "parent": "123456789",
        "todo": "Read *War and Peace*",
        "setting": "Finished reading *The Cat and the Hat* while watching a very
        orange sunset.",
        "body": "Today was a bright and sunny day!"
    }

    :param file_path: full path of the file
    :type file_path: string

    :return: json
    """
    with open(file_path, 'r') as f:
        (metadata, body) = f.read().split('\n\n', maxsplit=1)

        def parse_metadata(line):
            """
            :param line: line for metadata e.g. "Author: John Doe"
            :type line: string

            :return: (key string, value string)
            """
            m = re.search('^(\w*): (.*)', line)
            # Watch! Stripping trailing whitespace because for some reason
            # certain field values are showing whitespace.
            return m.group(1).lower(), m.group(2).strip()

        t = [ parse_metadata(line) for line in metadata.split('\n') ]

        response = dict(t)

        if "tags" in response:
            response['tags'] = response['tags'].split(', ')
            # Handle scenario when there are no tags which will return an empty
            # string. Also strip the unnecessary whitespaces.
            response['tags'] = [ tag.strip() for tag in response['tags'] if tag ]
        if body.strip():
            response['body'] = body

        return response

def create_filepath(file_dir, file_name):
    """
    TODO: Need test
    """
    file_name = file_name if ".md" in file_name else "{0}.md".format(file_name)
    return os.path.join(file_dir, file_name)

def generate_id(some_datetime):
    # WATCH! datetime.fromtimestamp(0) is not Unix epoch and returns
    # 1969-12-31 19:00 instead.
    epoch = datetime(1970, 1, 1)
    return str(int((some_datetime - epoch).total_seconds()))


if "__main__" == __name__:
    parser = argparse.ArgumentParser(description='Jarvis is used for personal information management')

    parser.add_argument('-e', '--environment', nargs='?', default="default",
            help="Jarvis environment name found in the cli_config.ini")
    parser.add_argument('--config-path', nargs='?', default=config.JARVIS_CLI_CONFIG_PATH,
            help="Path to Jarvis cli configuration file")

    subparsers = parser.add_subparsers(help='Actions for Jarvis',
            dest='action_name')

    # New actions
    parser_new = subparsers.add_parser('new', help='Create a new Jarvis resource')
    subparsers_new = parser_new.add_subparsers(help='Types of Jarvis resources',
            dest='resource_type')

    parser_new_log = subparsers_new.add_parser('log', help='Create a new log entry')
    parser_new_log.add_argument('-e', '--event-id', nargs='?', required=True,
            help='Associated event')

    parser_new_tag = subparsers_new.add_parser('tag', help='Create a new tag')
    parser_new_tag.add_argument('tag_name', help='Tag name')
    parser_new_event = subparsers_new.add_parser('event', help='Create a new event')

    # Edit actions
    parser_edit = subparsers.add_parser('edit', help='Edit an information element')
    subparsers_edit = parser_edit.add_subparsers(help='Types of information element',
            dest='resource_type')

    parser_edit_log = subparsers_edit.add_parser('log', help='Edit an existing log entry')
    parser_edit_log.add_argument('log_entry_name', help='Log name')
    parser_edit_log.add_argument('-e', '--event-id', nargs='?', required=True,
            help='Associated event')

    parser_edit_tag = subparsers_edit.add_parser('tag', help='Edit an existing tag element')
    parser_edit_tag.add_argument('tag_name', help='Tag name')

    parser_edit_event = subparsers_edit.add_parser('event', help='Edit event')
    parser_edit_event.add_argument('event_id', help='Event id')

    # Show actions
    parser_show = subparsers.add_parser('show', help='Show information elements')
    subparsers_show = parser_show.add_subparsers(help='Types of show actions',
            dest='resource_type')

    # TODO: Reimplement
    #parser_show_lastlog = subparsers_show.add_parser('lastlog',
    #        help='Open last log entry in the browser')
    #parser_show_lastlog.add_argument('-t', '--tag', nargs='?', help='Tag to search')

    parser_show_log = subparsers_show.add_parser('log', help='Open log entry in the browser')
    parser_show_log.add_argument('log_entry_name', help='Log name')
    parser_show_log.add_argument('-e', '--event-id', nargs='?', required=True,
            help='Associated event')

    parser_show_tag = subparsers_show.add_parser('tag', help='Open tag in the browser')
    parser_show_tag.add_argument('tag_name', help='Tag name')

    parser_show_event = subparsers_show.add_parser('event', help='Get and show event')
    parser_show_event.add_argument('event_id', help='Event id')

    # List actions
    parser_list = subparsers.add_parser('list', help='List Jarvis resources')
    subparsers_list = parser_list.add_subparsers(help='Types of list actions',
            dest='listing_type')

    parser_list_tags = subparsers_list.add_parser('tags', help='List tags')
    parser_list_tags.add_argument('-n', '--tag-name', nargs='?', help='Search by tag name')
    parser_list_tags.add_argument('-a', '--assoc-tags', nargs='?',
        help='Search by associated tags')

    parser_list_logs = subparsers_list.add_parser('logs', help='List log entries')
    parser_list_logs.add_argument('-t', '--tag', nargs='?', help='Tag to search')
    parser_list_logs.add_argument('-s', '--search', nargs='?', dest='search_term',
            help='Search term')

    parser_list_events = subparsers_list.add_parser('events', help='List events')
    parser_list_events.add_argument('-c', '--category', nargs='?',
            choices=jc.EVENT_CATEGORIES, help='Event category')
    parser_list_events.add_argument('-w', '--weight', nargs='?', type=int,
            help='Event weight lower bound')

    # Data summary
    parser_summary = subparsers.add_parser('summary', help='Show data summary')

    # Admin actions
    parser_admin = subparsers.add_parser('admin', help='Administrative actions')
    subparsers_admin = parser_admin.add_subparsers(help='Types of admin actions',
            dest='admin_type')

    parser_admin_backup = subparsers_admin.add_parser('backup',
            help='Create a new snapshot')

    parser_admin_restore = subparsers_admin.add_parser('restore',
            help='Restore from an existing snapshot')
    parser_admin_restore.add_argument('--snapshot-path', nargs='?', required=True,
            help='Path to snapshot used to restore')

    args = parser.parse_args()

    # NOTE: Argparse should filter and validate and ensure that only the known
    # choices get through to this point.
    # UPDATE: There is a case where the subsubparser allows for Nones to slip
    # through. The required flag doesn't seem to be reinforced so the following
    # is acceptable to Argparse which sucks for me:
    #   jarvis.py new

    config_map = config.get_config_map(args.environment, args.config_path)
    DBCONN = config.get_client_connection(config_map)

    def open_file_in_editor(filepath):
        editor = os.environ['EDITOR']
        subprocess.call([editor, filepath])

    # Modified not allowed for edits but want in reads. Split them up.
    metadata_keys_tag_show = ["name", "author", "created", "modified", "version",
            "tags"]
    metadata_keys_log_show = ["id", "author", "created", "modified", "version",
            "tags", "parent", "event", "todo"]
    metadata_keys_event_show = ["eventId", "created", "occurred", "category",
            "source", "weight", "description"]
    metadata_keys_tag_edit = [field for field in metadata_keys_tag_show if field
            not in ["modified"]]
    metadata_keys_log_edit = [field for field in metadata_keys_log_show if field
            not in ["event", "modified"]]
    metadata_keys_event_edit = [field for field in metadata_keys_event_show if field
            not in ["eventId", "created"]]

    def handle_jarvis_resource(metadata_keys, json_object, resource_id):
        if not json_object:
            return

        temp = "/tmp/{0}.md".format(resource_id)

        def convert_json_to_file(metadata_keys, json_object):
            def stringify(metadata_key):
                if metadata_key == "tags":
                    return ", ".join(json_object.get(metadata_key))
                else:
                    # Don't want to display literally "None" so check for None
                    # and convert to empty string.
                    v = json_object.get(metadata_key)
                    return v if v else ""

            metadata = [ "{0}: {1}".format(k.capitalize(), stringify(k))
                    for k in metadata_keys ]
            metadata = "\n".join(metadata)

            # Events don't have bodies
            if "body" in json_object:
                return "\n\n".join([ metadata, json_object.get("body") ])
            else:
                # HACK: The hardcoded "\n\n" is necessary bc
                # convert_file_to_json expects it.
                return metadata + "\n\n"

        with open(temp, 'w') as f:
            f.write(convert_json_to_file(metadata_keys, json_object))

        return temp

    def edit_file(metadata_keys, json_object, resource_id):
        temp = handle_jarvis_resource(metadata_keys, json_object, resource_id)

        if temp:
            open_file_in_editor(temp)
            return temp

    edit_file_tag = partial(edit_file, metadata_keys_tag_edit)
    edit_file_log = partial(edit_file, metadata_keys_log_edit)
    edit_file_event = partial(edit_file, metadata_keys_event_edit)

    def show_file(metadata_keys, json_object, resource_id):
        temp = handle_jarvis_resource(metadata_keys, json_object, resource_id)

        if temp:
            # Previews the markdown. This will require you to change the
            # mimeapps.list setting file in order to chose your markdown preview
            # tool.
            webbrowser.open("file://{0}".format(temp))

    show_file_tag = partial(show_file, metadata_keys_tag_show)
    show_file_log = partial(show_file, metadata_keys_log_show)
    show_file_event = partial(show_file, metadata_keys_event_show)

    def check_and_create_missing_tags(resource_request):
        for tag_name in resource_request['tags']:
            print("Checking if tag already exists: {0}".format(tag_name))
            if not get_tag(DBCONN, tag_name.lower()):
                try:
                    create_file_tag(tag_name)
                except Exception as e:
                    # TODO: Need to handle case when not all the tags gets created.
                    print("Unexpected error creating tag: {0}, {1}".format(
                        tag_name, e))

    def create_file(post_func, show_file_func, resource_id_key, local_path,
            stub_content):
        with open(local_path, 'w') as f:
            f.write(stub_content)

        open_file_in_editor(local_path)
        resource_request = convert_file_to_json(local_path)
        check_and_create_missing_tags(resource_request)
        resource = post_func(resource_request)

        if resource:
            resource_id = resource[resource_id_key]
            show_file_func(resource, resource_id)
            print("Created: {0}".format(resource_id))

    AUTHOR = config.get_author(config_map)

    def create_file_log(event_id):
        created = datetime.utcnow().replace(microsecond=0)

        metadata = [("Author", AUTHOR), ("Tags", None), ("Parent", None),
                ("Todo", None)]
        metadata = [ "{0}: {1}".format(k, v if v else "")
                for k, v in metadata ]
        stub_content = "\n".join(metadata)

        # Need a temporary log id because the log id actually gets created by
        # the API.
        log_id_temp = "jarvis_log_{0}" \
            .format(generate_id(created))

        log_path = create_filepath("/tmp", log_id_temp)

        create_file(partial(cle.post_log_entry, event_id, DBCONN), show_file_log,
                "id", log_path, stub_content)

    def create_file_tag(tag_name):
        metadata = [ "Name: {0}".format(tag_name),
                "Author: {0}".format(AUTHOR),
                "Tags: " ]

        stub_content = "\n\n".join(["\n".join(metadata), "# {0}\n".format(tag_name)])
        tag_path = create_filepath("/tmp", tag_name)

        create_file(partial(post_tag, DBCONN), show_file_tag,
                "name", tag_path, stub_content)


    if args.action_name == 'new':

        if args.resource_type == 'log':
            create_file_log(args.event_id)
        elif args.resource_type == 'tag':
            print("Checking if tag already exists: {0}".format(args.tag_name))

            if get_tag(DBCONN, args.tag_name.lower()):
                print("Tag already exists: {0}".format(args.tag_name))
            else:
                create_file_tag(args.tag_name)
        elif args.resource_type == 'event':
            occurred = dateparser.parse(input("When occurred [default: now]?: "))
            occurred = occurred or datetime.utcnow()

            while True:
                category = input("Event category [options: {0}]: ".format(
                    jc.EVENT_CATEGORIES))

                if category in jc.EVENT_CATEGORIES:
                    break

            while True:
                default = jc.EVENT_CATEGORIES_TO_DEFAULTS.get(category)
                weight = input("Event weight [default: {0}]: ".format(default)) \
                    or default

                try:
                    weight = int(weight)
                    break
                except:
                    pass

            filepath = create_filepath("/tmp",
                    "jarvis_event_{0}".format(generate_id(occurred)))
            open_file_in_editor(filepath)

            with open(filepath, 'r') as f:
                description = f.read()

            request = { "occurred": occurred.isoformat(), "category": category,
                    "source": "jarvis-cli:{0}".format(jc.__version__),
                    "weight": weight, "description": description }
            response = post_event(DBCONN, request)

            if response:
                print("Created: {0}".format(response.get("eventId")))
        else:
            raise NotImplementedError("Unknown information type: {0}"
                    .format(args.resource_type))

    elif args.action_name == 'edit':

        def edit_resource(get_func, put_func, edit_file_func, show_file_func,
                post_edit_func, resource_id):
            resource = get_func(DBCONN, resource_id)

            if resource:
                filepath = edit_file_func(resource, resource_id)

                if filepath:
                    json_object = convert_file_to_json(filepath)
                    json_object = post_edit_func(json_object)

                    resource = put_func(DBCONN, resource_id, json_object)

                    if resource:
                        show_file_func(resource, resource_id)
                        print("Editted: {0}".format(resource_id))

        if args.resource_type == 'log':
            def post_edit_log(json_object):
                # WATCH! This specialty code here because the LogEntry.id
                # is a number.
                json_object["id"] = int(json_object["id"])
                check_and_create_missing_tags(json_object)

                # Change from log entry to log entry request
                json_object.pop('created', None)
                json_object.pop('id', None)
                json_object.pop('version', None)
                return json_object

            # TODO: There must be a easier way to get event id.
            get_func = partial(cle.get_log_entry, args.event_id)
            put_func = partial(cle.put_log_entry, args.event_id)

            edit_resource(get_func, put_func, edit_file_log,
                    show_file_log, post_edit_log, args.log_entry_name)
        elif args.resource_type == 'tag':
            def post_edit_tag(json_object):
                check_and_create_missing_tags(json_object)

                # Change from tag to tag request
                json_object.pop("created", None)
                json_object.pop("version", None)
                return json_object

            edit_resource(client.get_tag, client.put_tag, edit_file_tag, show_file_tag,
                    post_edit_tag, args.tag_name)
        elif args.resource_type == 'event':
            def post_edit_event(json_object):
                json_object["weight"] = int(json_object["weight"])
                return json_object

            edit_resource(client.get_event, client.put_event, edit_file_event,
                    show_file_event, post_edit_event, args.event_id)

    elif args.action_name == 'show':

        def get_and_show_resource(get_func, show_file_func, resource_id):
            resource = get_func(DBCONN, resource_id)
            show_file_func(resource, resource_id)

        if args.resource_type == 'tag':
            get_and_show_resource(client.get_tag, show_file_tag, args.tag_name)
        elif args.resource_type == 'log':
            # TODO: There must be a easier way to get event id.
            get_func = partial(cle.get_log_entry, args.event_id)
            get_and_show_resource(get_func, show_file_log, args.log_entry_name)
        elif args.resource_type == "event":
            get_and_show_resource(client.get_event, show_file_event, args.event_id)

    elif args.action_name == 'list':

        if args.listing_type == 'tags':
            tags = query("tags", DBCONN, [("name", args.tag_name),
                ("tags", args.assoc_tags)])

            if tags:
                tags = [ [tag['name'], ",".join(tag['tags'])] for tag in tags ]
                print(tabulate(tags, ["tag name", "tags"], tablefmt="simple"))
            else:
                print("No tags found")
        elif args.listing_type == 'logs':
            logs = cle.query_log_entries(DBCONN, [("tags", args.tag),
                ("searchterm", args.search_term)])

            if logs:
                def create_summary(log):
                    """
                    Form a summary representation of the log file.
                    """
                    try:
                        event_id = log["event"]
                        event = client.get_event(DBCONN, event_id)
                    except Exception as e:
                        import pprint
                        pprint.pprint(log)
                        raise e

                    def format_ids():
                        return "{0} -e {1}".format(log["id"], log["event"])

                    def format_timestamps():
                        def iso_to_datetime(str_datetime):
                            return dateparser.parse(str_datetime)

                        created = iso_to_datetime(log['created'])
                        occurred = iso_to_datetime(event['occurred'])
                        delta = (created - occurred).total_seconds()
                        dates = { "created": log["created"],
                                "occurred": event["occurred"],
                                "delta": int(delta/3600) }

                        return "Occurred: {0}, Created: {1}, Delta: {2}hrs" \
                            .format(dates["occurred"], dates["created"], dates["delta"])

                    def format_tags():
                        return "Tags: {0}".format(", ".join(log["tags"]))

                    def format_blurb():
                        return log['body'].split('\n')[0][0:250]

                    return "\n".join([func() for func in [format_ids, format_timestamps,
                        format_tags, format_blurb]])

                def parse(log):
                    if args.search_term:
                        # This regex will look for a search term and grab 60 characters
                        # around the matched term.
                        search_regex = re.compile('.{{0,30}}\S*{0}\S*.{{0,30}}'
                                .format(args.search_term), re.IGNORECASE)

                        def find_search_term(log):
                            """
                            :return: List of the matched strings
                            """
                            return [ m.group(0) for m in
                                    search_regex.finditer(log['body']) ]

                        def format_matches(matches):
                            if matches:
                                return "\n".join([ "[{0}]: \"{1}\"".format(i, matches[i])
                                    for i in range(0, len(matches)) ])
                            else:
                                return "No matches"

                        return "\n\nSearch matches:\n".join([ create_summary(log),
                             format_matches(find_search_term(log)) ])
                    else:
                        return create_summary(log)

                logs = [ parse(log) for log in reversed(logs) ]
                print("\n\n".join(logs))
                print("\n\nLog entries found: {0}".format(len(logs)))
            else:
                print("No log entries found")
        elif args.listing_type == 'events':
            # TODO: Show table view vs list view
            query_params = [('category', args.category), ('weight', args.weight)]
            query_params = [ qp for qp in query_params if qp[1] != None ]

            events = query('events', DBCONN, query_params)

            if events:
                fields = ['category', 'occurred', 'weight', 'description', 'eventId']

                def show_event(e):
                    def truncate_string(e):
                        cutoff = 40
                        return e[:cutoff] if isinstance(e, str) and len(e) > cutoff \
                            else e

                    return [ truncate_string(e[field]) for field in fields ]

                events = [ show_event(e) for e in events ]
                print(tabulate(events, fields, tablefmt="simple"))
            else:
                print("No events found")
        else:
            raise NotImplementedError("Unknown listing type: {0}"
                    .format(args.show_type))

    elif args.action_name == 'summary':

        columns = list(get_data_summary("tags", DBCONN).keys())
        summaries = [ list(get_data_summary(rt, DBCONN).values())
                for rt in ["tags", "logentries", "events"] ]
        print(tabulate(summaries, columns, tablefmt="simple"))

    elif args.action_name == 'admin':

        if args.admin_type == 'backup':
            filepath = admin.create_snapshot(args.environment, config_map)

            if filepath:
                print("Backing up successful: {0}".format(filepath))
            else:
                print("Backing up failed")
        elif args.admin_type == 'restore':
            if admin.restore_snapshot(config_map, args.snapshot_path):
                print("Restore successful")
            else:
                print("Restore failed")
