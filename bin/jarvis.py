#! python

import os, subprocess, argparse, re
from functools import partial
import webbrowser
from datetime import datetime
from tabulate import tabulate
from jarvis_cli.client import DBConn, get_tag, get_log_entry, put_log_entry, \
    put_tag, post_log_entry, post_tag, query, get_data_summary


DBCONN = DBConn("localhost", "3000")

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
        response['tags'] = response['tags'].split(', ')
        # Handle scenario when there are no tags which will return an empty
        # string. Also strip the unnecessary whitespaces.
        response['tags'] = [ tag.strip() for tag in response['tags'] if tag ]
        response['body'] = body
        return response

def create_filepath(file_dir, file_name):
    """
    TODO: Need test
    """
    file_name = file_name if ".md" in file_name else "{0}.md".format(file_name)
    return os.path.join(file_dir, file_name)


if "__main__" == __name__:
    parser = argparse.ArgumentParser(description='Jarvis is used for personal information management')

    subparsers = parser.add_subparsers(help='Actions for Jarvis',
            dest='action_name')

    # New actions
    parser_new = subparsers.add_parser('new', help='Create an information element')
    subparsers_new = parser_new.add_subparsers(help='Types of new information element',
            dest='element_type')
    parser_new_log = subparsers_new.add_parser('log', help='Create a new log entry')
    parser_new_tag = subparsers_new.add_parser('tag', help='Create a new tag element')
    parser_new_tag.add_argument('tag_name', help='Tag name')

    # Edit actions
    parser_edit = subparsers.add_parser('edit', help='Edit an information element')
    subparsers_edit = parser_edit.add_subparsers(help='Types of information element',
            dest='element_type')

    parser_edit_log = subparsers_edit.add_parser('log', help='Edit an existing log entry')
    parser_edit_log.add_argument('log_entry_name', help='Log name')

    parser_edit_tag = subparsers_edit.add_parser('tag', help='Edit an existing tag element')
    parser_edit_tag.add_argument('tag_name', help='Tag name')

    # Show actions
    parser_show = subparsers.add_parser('show', help='Show information elements')
    subparsers_show = parser_show.add_subparsers(help='Types of show actions',
            dest='show_type')

    parser_show_lastlog = subparsers_show.add_parser('lastlog',
            help='Open last log entry in the browser')
    parser_show_lastlog.add_argument('-t', '--tag', nargs='?', help='Tag to search')

    parser_show_log = subparsers_show.add_parser('log', help='Open log entry in the browser')
    parser_show_log.add_argument('log_entry_name', help='Log name')

    parser_show_tag = subparsers_show.add_parser('tag', help='Open tag in the browser')
    parser_show_tag.add_argument('tag_name', help='Tag name')

    # List actions
    parser_list = subparsers.add_parser('list', help='List information elements')
    subparsers_list = parser_list.add_subparsers(help='Types of list actions',
            dest='listing_type')

    parser_list_tags = subparsers_list.add_parser('tags', help='List all tags')
    parser_list_tags.add_argument('-n', '--tag-name', nargs='?', help='Search by tag name')
    parser_list_tags.add_argument('-a', '--assoc-tags', nargs='?',
        help='Search by associated tags')

    parser_list_logs = subparsers_list.add_parser('logs', help='List all logs')
    parser_list_logs.add_argument('-t', '--tag', nargs='?', help='Tag to search')
    parser_list_logs.add_argument('-s', '--search', nargs='?', dest='search_term',
            help='Search term')

    # Data summary
    parser_summary = subparsers.add_parser('summary', help='Show data summary')

    args = parser.parse_args()

    # NOTE: Argparse should filter and validate and ensure that only the known
    # choices get through to this point.
    # UPDATE: There is a case where the subsubparser allows for Nones to slip
    # through. The required flag doesn't seem to be reinforced so the following
    # is acceptable to Argparse which sucks for me:
    #   jarvis.py new

    def open_file_in_editor(filepath):
        editor = os.environ['EDITOR']
        subprocess.call([editor, filepath])

    # Modified not allowed for edits but want in reads. Split them up.
    metadata_keys_tag_show = ["name", "author", "created", "modified", "version",
            "tags"]
    metadata_keys_log_show = ["id", "author", "created", "modified", "occurred",
            "version", "tags", "parent", "event", "todo", "setting"]
    metadata_keys_tag_edit = [field for field in metadata_keys_tag_show if field
            not in ["modified"]]
    metadata_keys_log_edit = [field for field in metadata_keys_log_show if field
            not in ["modified"]]

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

            return "\n\n".join([ metadata, json_object.get("body") ])

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

    def show_file(metadata_keys, json_object, resource_id):
        temp = handle_jarvis_resource(metadata_keys, json_object, resource_id)

        if temp:
            # Previews the markdown. This will require you to change the
            # mimeapps.list setting file in order to chose your markdown preview
            # tool.
            webbrowser.open("file://{0}".format(temp))

    show_file_tag = partial(show_file, metadata_keys_tag_show)
    show_file_log = partial(show_file, metadata_keys_log_show)

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

    AUTHOR = os.environ['JARVIS_AUTHOR']

    def create_file_log():
        created = datetime.utcnow().replace(microsecond=0)

        metadata = [ ("Author", AUTHOR), ("Occurred", created.isoformat()),
                ("Tags", None), ("Parent", None), ("Event", None), ("Todo", None),
                ("Setting", None) ]
        metadata = [ "{0}: {1}".format(k, v if v else "")
                for k, v in metadata ]
        stub_content = "\n".join(metadata)

        # datetime.fromtimestamp(0) is not Unix epoch and returns
        # 1969-12-31 19:00 instead.
        epoch = datetime(1970, 1, 1)
        # Need a temporary log id because the log id actually gets created by
        # the API.
        log_id_temp = "jarvis_log_{0}" \
            .format(str(int((created - epoch).total_seconds())))

        log_path = create_filepath("/tmp", log_id_temp)

        create_file(partial(post_log_entry, DBCONN), show_file_log,
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

        if args.element_type == 'log':
            create_file_log()
        elif args.element_type == 'tag':
            print("Checking if tag already exists: {0}".format(args.tag_name))

            if get_tag(DBCONN, args.tag_name.lower()):
                print("Tag already exists: {0}".format(args.tag_name))
            else:
                create_file_tag(args.tag_name)
        else:
            raise NotImplementedError("Unknown information type: {0}"
                    .format(args.element_type))

    elif args.action_name == 'edit':

        # TODO: DRY this code?

        if args.element_type == 'log':
            log_entry = get_log_entry(DBCONN, args.log_entry_name)

            if log_entry:
                filepath = edit_file_log(log_entry, log_entry["id"])

                if filepath:
                    json_object = convert_file_to_json(filepath)
                    # WATCH! This specialty code here because the LogEntry.id
                    # is a number.
                    json_object["id"] = int(json_object["id"])
                    check_and_create_missing_tags(json_object)

                    # Change from log entry to log entry request
                    json_object.pop('created', None)
                    json_object.pop('id', None)
                    json_object.pop('version', None)

                    log_entry = put_log_entry(DBCONN, args.log_entry_name, json_object)

                    if log_entry:
                        show_file_log(log_entry, args.log_entry_name)
                        print("Editted: {0}, {1}".format(args.element_type,
                            args.log_entry_name))
        elif args.element_type == 'tag':
            tag = get_tag(DBCONN, args.tag_name)

            if tag:
                filepath = edit_file_tag(tag, tag["name"])

                if filepath:
                    json_object = convert_file_to_json(filepath)
                    check_and_create_missing_tags(json_object)

                    # Change from tag to tag request
                    json_object.pop("created", None)
                    json_object.pop("version", None)

                    tag = put_tag(DBCONN, args.tag_name, json_object)

                    if tag:
                        show_file_tag(tag, args.tag_name)
                        print("Editted: {0}, {1}".format(args.element_type,
                            args.tag_name))

    elif args.action_name == 'show':

        def get_and_show_log(log_id):
            log_entry = get_log_entry(DBCONN, log_id)
            show_file_log(log_entry, log_id)

        if args.show_type == 'tag':
            tag = get_tag(DBCONN, args.tag_name)
            show_file_tag(tag, args.tag_name)
        elif args.show_type == 'log':
            get_and_show_log(args.log_entry_name)
        else:
            raise NotImplementedError("Unknown show type: {0}"
                    .format(args.show_type))

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
            logs = query("logentries", DBCONN, [("tags", args.tag),
                ("searchterm", args.search_term)])

            if logs:
                def create_summary(log):
                    """
                    Form a summary representation of the log file.
                    """
                    def iso_to_datetime(str_datetime):
                        return datetime.strptime(str_datetime, '%Y-%m-%dT%H:%M:%S')

                    created = iso_to_datetime(log['created'])
                    occurred = iso_to_datetime(log['occurred'])

                    delta = (created - occurred).total_seconds()
                    dates = "Occurred: {0}, Created: {1}, Delta: {2}hrs" \
                        .format(log['occurred'], log['created'], int(delta/3600))

                    if log['setting'] == "N/A":
                        # Clip the body
                        clip = log['body'].split('\n')[0][0:250]
                    else:
                        clip = log['setting']
                    return "\n".join([str(log['id']), dates,
                        ", ".join(log['tags']), clip])

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
        else:
            raise NotImplementedError("Unknown listing type: {0}"
                    .format(args.show_type))

    elif args.action_name == 'summary':

        columns = list(get_data_summary("tags", DBCONN).keys())
        summaries = [ list(get_data_summary(rt, DBCONN).values())
                for rt in ["tags", "logentries"] ]
        print(tabulate(summaries, columns, tablefmt="simple"))
