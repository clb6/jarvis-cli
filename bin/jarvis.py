#!/usr/bin/env python

import os, subprocess, argparse, re
from collections import namedtuple
from operator import itemgetter
import webbrowser
from datetime import datetime

class JarvisSettings(object):

    def __init__(self):
        # TODO: Make a test mode where it writes to a test directory.
        self._env_dir_jarvis_root = os.environ['JARVIS_DIR_ROOT']
        self._env_author = os.environ['JARVIS_AUTHOR']
        self._version_log = "0.2.0"
        self._version_tag = "0.1.0"

    @property
    def root_directory(self):
        return self._env_dir_jarvis_root

    def _create_directory(self, sub_directory):
        return "{0}/{1}".format(self.root_directory, sub_directory)

    @property
    def images_directory(self):
        return self._create_directory('Images')

    @property
    def logs_directory(self):
        return self._create_directory('LogEntries')

    @property
    def tags_directory(self):
        return self._create_directory('Tags')

    @property
    def author(self):
        return self._env_author

    @property
    def log_version(self):
        return self._version_log

    @property
    def tag_version(self):
        return self._version_tag


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
            return m.group(1).lower(), m.group(2)

        t = [ parse_metadata(line) for line in metadata.split('\n') ]

        response = dict(t)
        response['tags'] = response['tags'].split(', ')
        # Handle scenario when there are no tags which will return an empty
        # string.
        response['tags'] = [ tag for tag in response['tags'] if tag ]
        response['body'] = body
        return response

def create_filepath(file_dir, file_name):
    """
    TODO: Need test
    """
    file_name = file_name if ".md" in file_name else "{0}.md".format(file_name)
    return "{0}/{1}".format(file_dir, file_name)

JarvisContext = namedtuple('JarvisContext', ['file_name', 'file_path'])

def create_context(file_dir, file_name):
    return JarvisContext(file_name, create_filepath(file_dir, file_name))

class JarvisTagError(RuntimeError):
    pass

def get_tags(jarvis_settings):
    """
    :return: iterable of just tag names
    """
    return map(lambda e: e[0], get_tags_with_relations(jarvis_settings))

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

    def edit_file(context):
        if not os.path.isfile(context.file_path):
            raise IOError("File does not exist! {0}".format(context.file_path))
        open_file_in_editor(context.file_path)

    def show_file_with_images(context):
        if not os.path.isfile(context.file_path):
            raise IOError("File does not exist! {0}".format(context.file_path))

        images_pattern = '!\[(\w*)\]\(([\w.\/]*)\)'
        # The "\1" and "\2" gets replaced with the regex groups.
        images_link = "<img src=\"file://{0}/\\2\" alt=\"\\1\" height=\"750px\" width=\"750px\" />" \
            .format(js.images_directory)

        # Look for markdown images and transform to html images with the
        # appropriate directory.  Plus I can resize the image here.

        with open(context.file_path, 'r') as f:
            old_text = f.read()

        temp = "/tmp/{0}.md".format(context.file_name)

        with open(temp, 'w') as f:
            f.write(re.sub(images_pattern, images_link, old_text))

        # Previews the markdown. This will require you to change the
        # mimeapps.list setting file in order to chose your markdown preview
        # tool.
        webbrowser.open("file://{0}".format(temp))

    def show_file(filepath):
        if not os.path.isfile(filepath):
            raise IOError("File does not exist! {0}".format(filepath))

        # Previews the markdown. This will require you to change the
        # mimeapps.list setting file in order to chose your markdown preview
        # tool.
        filepath_browser = "file://{0}".format(filepath)
        webbrowser.open(filepath_browser)

    def create_file(filepath, element_type):
        if filepath:
            open_file_in_editor(filepath)
            show_file(filepath)
            print("Created: {0}, {1}".format(element_type, filepath))
            check_and_create_missing_tags(filepath)
        else:
            print("Failed to create new information element")

    def create_stub_file(dir_target, filename, metadata):
        filepath = create_filepath(dir_target, filename)

        if os.path.isfile(filepath):
            raise IOError("File already exists! {0}".format(filepath))

        with open(filepath, 'w') as f:
            for metadatum in metadata:
                f.write(metadatum)

        return filepath

    def create_tag(tag_name):
        created = datetime.utcnow().replace(microsecond=0)

        metadata = [ "Author: {0}\n".format(js.author),
                "Created: {0}\n".format(created.isoformat()),
                "Version: {0}\n".format(js.tag_version),
                "Tags: \n" ]

        filepath = create_stub_file(js.tags_directory, tag_name, metadata)

        # Add the title which should be the tag name
        with open(filepath, 'a') as f:
            # TODO: Would be very cool to reinforce camel case for the file
            # name and canonical for title.
            f.write("\n# {0}\n".format(tag_name))

        create_file(filepath, 'tag')

    def check_and_create_missing_tags(filepath):
        json_rep = convert_file_to_json(filepath)
        new_tags = set(json_rep['tags'])
        existing_tags = set(get_tags(js))

        # TODO: Need to handle case when not all the tags gets created. At least
        # print the name of the tags that didn't get created.
        for tag_name in new_tags.difference(existing_tags):
            create_tag(tag_name)


    if args.action_name == 'new':

        if args.element_type == 'log':
            created = datetime.utcnow().replace(microsecond=0)

            metadata = [ "Author: {0}\n".format(js.author),
                    "Created: {0}\n".format(created.isoformat()),
                    "Occurred: {0}\n".format(created.isoformat()),
                    "Version: {0}\n".format(js.log_version),
                    "Tags: \n" ]

            # datetime.fromtimestamp(0) is not Unix epoch and returns
            # 1969-12-31 19:00 instead.
            epoch = datetime(1970, 1, 1)

            filepath = create_stub_file(js.logs_directory,
                str(int((created - epoch).total_seconds())), metadata)

            create_file(filepath, args.element_type)
        elif args.element_type == 'tag':
            create_tag(args.tag_name)
        else:
            raise NotImplementedError("Unknown information type: {0}"
                    .format(args.element_type))

    elif args.action_name == 'edit':

        if args.element_type == 'log':
            context = create_context(js.logs_directory, args.log_entry_name)
        elif args.element_type == 'tag':
            context = create_context(js.tags_directory, args.tag_name)
        else:
            raise NotImplementedError("Unknown information type: {0}"
                    .format(args.element_type))

        edit_file(context)
        show_file_with_images(context)
        print("Editted: {0}, {1}".format(args.element_type, context.file_path))
        check_and_create_missing_tags(context.file_path)

    elif args.action_name == 'show':

        if args.show_type == 'tag':
            show_file_with_images(create_context(js.tags_directory,
                args.tag_name))
        elif args.show_type == 'lastlog':
            is_found = False

            for log_file in sorted(os.listdir(js.logs_directory), reverse=True):
                context = create_context(js.logs_directory, log_file)

                if args.tag:
                    json_rep = convert_file_to_json(log_path)

                    if any([args.tag.lower() in tag.lower()
                        for tag in json_rep['tags']]):
                        show_file_with_images(context)
                        is_found = True
                        break
                else:
                    show_file_with_images(context)
                    is_found = True
                    break

            if not is_found:
                print("There is no log entry for \"{0}\"".format(args.tag))
        elif args.show_type == 'log':
            show_file_with_images(create_context(js.logs_directory,
                args.log_entry_name))
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

                if src_json['version'] == '0.2.0':
                    src_json['occurred'] = iso_to_datetime(src_json['occurred'])
                else:
                    # Temporary
                    src_json['occurred'] = src_json['created']

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
