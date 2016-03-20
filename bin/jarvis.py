#! python

import os, subprocess, argparse, re, json
from collections import namedtuple
from operator import itemgetter
from functools import partial
import webbrowser
from datetime import datetime
import urllib
import requests

class JarvisSettings(object):

    def __init__(self):
        # TODO: Make a test mode where it writes to a test directory.
        self._env_dir_jarvis_root = os.environ['JARVIS_DIR_ROOT']
        self._env_author = os.environ['JARVIS_AUTHOR']

    @property
    def root_directory(self):
        return self._env_dir_jarvis_root

    def _create_directory(self, sub_directory):
        return "{0}/{1}".format(self.root_directory, sub_directory)

    @property
    def logs_directory(self):
        return self._create_directory('LogEntries')

    @property
    def tags_directory(self):
        return self._create_directory('Tags')

    @property
    def author(self):
        return self._env_author


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

class JarvisTagError(RuntimeError):
    pass

def get_tags_with_relations(jarvis_settings):
    """
    :return: list of (tag name, list of related tags)
    """
    tag_pattern = re.compile('([\w&]*)\.md')

    def parse_tag(tag_file_name):
        """
        :return: tag name, list of related tags
        """
        try:
            filepath = create_filepath(jarvis_settings.tags_directory,
                    tag_file_name)
            json_rep = convert_file_to_json(filepath)
            return tag_pattern.search(tag_file_name).group(1), \
                json_rep['tags']
        except:
            raise JarvisTagError("Unexpected tag file name: {0}".format(tag_file_name))

    return [ parse_tag(tag_file_name) for tag_file_name in
            sorted(os.listdir(jarvis_settings.tags_directory)) ]

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
        print(json.dumps(resource_request))


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

    parser_list_logs = subparsers_list.add_parser('logs', help='List all logs')
    parser_list_logs.add_argument('-t', '--tag', nargs='?', help='Tag to search')
    parser_list_logs.add_argument('-s', '--search', nargs='?', dest='search_term',
            help='Search term')

    args = parser.parse_args()

    # NOTE: Argparse should filter and validate and ensure that only the known
    # choices get through to this point.
    # UPDATE: There is a case where the subsubparser allows for Nones to slip
    # through. The required flag doesn't seem to be reinforced so the following
    # is acceptable to Argparse which sucks for me:
    #   jarvis.py new

    js = JarvisSettings()

    def open_file_in_editor(filepath):
        editor = os.environ['EDITOR']
        subprocess.call([editor, filepath])

    metadata_keys_tag = ["name", "author", "created", "version", "tags"]
    metadata_keys_log = ["id", "author", "created", "occurred", "version", "tags",
            "parent", "todo", "setting"]

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

    edit_file_tag = partial(edit_file, metadata_keys_tag)
    edit_file_log = partial(edit_file, metadata_keys_log)

    def show_file(metadata_keys, json_object, resource_id):
        temp = handle_jarvis_resource(metadata_keys, json_object, resource_id)

        if temp:
            # Previews the markdown. This will require you to change the
            # mimeapps.list setting file in order to chose your markdown preview
            # tool.
            webbrowser.open("file://{0}".format(temp))

    show_file_tag = partial(show_file, metadata_keys_tag)
    show_file_log = partial(show_file, metadata_keys_log)

    def check_and_create_missing_tags(resource_request):
        for tag_name in resource_request['tags']:
            print("Checking if tag already exists: {0}".format(tag_name))
            if not get_tag(tag_name.lower()):
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

    def create_file_log():
        created = datetime.utcnow().replace(microsecond=0)

        metadata = [ ("Author", js.author), ("Occurred", created.isoformat()),
                ("Tags", None), ("Parent", None), ("Todo", None), ("Setting", None) ]
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

        create_file(partial(post_jarvis_resource, 'logentries'), show_file_log,
                "id", log_path, stub_content)

    def create_file_tag(tag_name):
        metadata = [ "Name: {0}".format(tag_name),
                "Author: {0}".format(js.author),
                "Tags: " ]

        stub_content = "\n\n".join(["\n".join(metadata), "# {0}\n".format(tag_name)])
        tag_path = create_filepath("/tmp", tag_name)

        create_file(partial(post_jarvis_resource, 'tags'), show_file_tag,
                "name", tag_path, stub_content)


    if args.action_name == 'new':

        if args.element_type == 'log':
            create_file_log()
        elif args.element_type == 'tag':
            print("Checking if tag already exists: {0}".format(args.tag_name))

            if get_tag(args.tag_name.lower()):
                print("Tag already exists: {0}".format(args.tag_name))
            else:
                create_file_tag(args.tag_name)
        else:
            raise NotImplementedError("Unknown information type: {0}"
                    .format(args.element_type))

    elif args.action_name == 'edit':

        # TODO: DRY this code?

        if args.element_type == 'log':
            log_entry = get_log_entry(args.log_entry_name)

            if log_entry:
                filepath = edit_file_log(log_entry, log_entry["id"])

                if filepath:
                    json_object = convert_file_to_json(filepath)
                    # WATCH! This specialty code here because the LogEntry.id
                    # is a number.
                    json_object["id"] = int(json_object["id"])
                    check_and_create_missing_tags(json_object)
                    log_entry = put_jarvis_resource("logentries",
                            args.log_entry_name, json_object)

                    if log_entry:
                        show_file_log(log_entry, args.log_entry_name)
                        print("Editted: {0}, {1}".format(args.element_type,
                            args.log_entry_name))
        elif args.element_type == 'tag':
            tag = get_tag(args.tag_name)

            if tag:
                filepath = edit_file_tag(tag, tag["name"])

                if filepath:
                    json_object = convert_file_to_json(filepath)
                    check_and_create_missing_tags(json_object)
                    tag = put_jarvis_resource("tags", args.tag_name, json_object)

                    if tag:
                        show_file_tag(tag, args.tag_name)
                        print("Editted: {0}, {1}".format(args.element_type,
                            args.tag_name))

    elif args.action_name == 'show':

        def get_and_show_log(log_id):
            log_entry = get_log_entry(log_id)
            show_file_log(log_entry, log_id)

        if args.show_type == 'tag':
            tag = get_tag(args.tag_name)
            show_file_tag(tag, args.tag_name)
        elif args.show_type == 'lastlog':
            is_found = False

            # TODO: Replace this with a web call
            for log_file in sorted(os.listdir(js.logs_directory), reverse=True):
                log_id = log_file.replace(".md", "")

                if args.tag:
                    json_rep = convert_file_to_json(log_path)

                    if any([args.tag.lower() in tag.lower()
                        for tag in json_rep['tags']]):
                        get_and_show_log(log_id)
                        is_found = True
                        break
                else:
                    get_and_show_log(log_id)
                    is_found = True
                    break

            if not is_found:
                print("There is no log entry for \"{0}\"".format(args.tag))
        elif args.show_type == 'log':
            get_and_show_log(args.log_entry_name)
        else:
            raise NotImplementedError("Unknown show type: {0}"
                    .format(args.show_type))

    elif args.action_name == 'list':

        if args.listing_type == 'tags':
            for tag, related_tags in get_tags_with_relations(js):
                print("{0} -> {1}".format(tag, ', '.join(related_tags)))
        elif args.listing_type == 'logs':
            entries = []

            # 1. Go through each log file
            # 2. Convert each file to json
            # 3. Filter by tag if need be
            # 4. Print entries

            def iso_to_datetime(str_datetime):
                return datetime.strptime(str_datetime, '%Y-%m-%dT%H:%M:%S')

            def convert_to_json_log(src_json, log_filename):
                src_json['created'] = iso_to_datetime(src_json['created'])
                src_json['log_filename'] = log_filename

                if src_json['version'] == '0.1.0':
                    # Temporary
                    src_json['occurred'] = src_json['created']
                else:
                    src_json['occurred'] = iso_to_datetime(src_json['occurred'])

                return src_json

            def create_summary(json_log):
                """
                Form a summary representation of the log file.
                """
                delta = (json_log['created'] - json_log['occurred']).total_seconds()
                dates = "Occurred: {0}, Created: {1}, Delta: {2}hrs".format(
                        json_log['occurred'].isoformat(),
                        json_log['created'].isoformat(),
                        int(delta/3600))

                if 'setting' in json_log:
                    clip = json_log['setting']
                else:
                    # Clip the body
                    clip = json_log['body'].split('\n')[0][0:250]
                return "\n".join([json_log['log_filename'], dates,
                    ", ".join(json_log['tags']), clip])

            json_logs = [ convert_to_json_log(convert_file_to_json(
                "{0}/{1}".format(js.logs_directory, log_filename)), log_filename)
                for log_filename in os.listdir(js.logs_directory) ]

            def is_tag_match(target_tag, json_log):
                """
                :return: Return True if no target tag to match against or if there
                is a tag match else False
                """
                return not target_tag or any([target_tag.lower() in tag.lower()
                    for tag in json_log['tags']])

            # This regex will look for a search term and grab 60 characters
            # around the matched term.
            search_regex = re.compile('.{{0,30}}\S*{0}\S*.{{0,30}}'.format(args.search_term),
                    re.IGNORECASE) if args.search_term else None

            def find_search_term(json_log):
                """
                :return: List of the matched strings
                """
                return [ m.group(0) for m in
                        search_regex.finditer(json_log['body']) ]

            # Sort order is in increasing time by Occurred datetime. The most
            # recent should be visible at the new command prompt.
            for json_log in sorted(json_logs, key=itemgetter('occurred')):
                if is_tag_match(args.tag, json_log):
                    if search_regex:
                        def format_matches(matches):
                            if matches:
                                return "\n".join([ "[{0}]: \"{1}\"".format(i, matches[i])
                                    for i in range(0, len(matches)) ])
                            else:
                                return "No matches"

                        entry = "\n\nSearch matches:\n".join([ create_summary(json_log),
                             format_matches(find_search_term(json_log)) ])
                        entries.append(entry)
                    else:
                        entries.append(create_summary(json_log))

            if entries:
                print("\n\n".join(entries))
                print("\n\nLog entries found: {0}".format(len(entries)))
            else:
                print("No log entries found")
        else:
            raise NotImplementedError("Unknown listing type: {0}"
                    .format(args.show_type))
