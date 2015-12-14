#!/usr/bin/env python

import os, subprocess, argparse, re
import webbrowser
from datetime import datetime

class JarvisSettings(object):

    def __init__(self):
        # TODO: Make a test mode where it writes to a test directory.
        self._env_dir_jarvis_root = os.environ['JARVIS_DIR_ROOT']
        self._env_author = os.environ['JARVIS_AUTHOR']
        self._env_version = "0.1.0"

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

    @property
    def document_version(self):
        return self._env_version


def convert_file_to_json(file_string):
    """
    Form a json representation of a log file.

    :param file_string: all of file content
    :type file_string: string
    """
    (metadata, body) = file_string.split('\n\n', maxsplit=1)

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
    response['body'] = body
    return response


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

    parser_show_logs = subparsers_show.add_parser('logs', help='List all logs')
    parser_show_logs.add_argument('-t', '--tag', nargs='?', help='Tag to search')

    parser_show_lastlog = subparsers_show.add_parser('lastlog',
            help='Open last log entry in the browser')
    parser_show_lastlog.add_argument('-t', '--tag', nargs='?', help='Tag to search')

    parser_show_log = subparsers_show.add_parser('log', help='Open log entry in the browser')
    parser_show_log.add_argument('log_entry_name', help='Log name')

    parser_show_tags = subparsers_show.add_parser('tags', help='List all tags')

    parser_show_tag = subparsers_show.add_parser('tag', help='Open tag in the browser')
    parser_show_tag.add_argument('tag_name', help='Tag name')

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

    def edit_file(filepath):
        if not os.path.isfile(filepath):
            raise IOError("File does not exist! {0}".format(filepath))
        open_file_in_editor(filepath)

    def show_file(filepath):
        if not os.path.isfile(filepath):
            raise IOError("File does not exist! {0}".format(filepath))

        # Previews the markdown. This will require you to change the
        # mimeapps.list setting file in order to chose your markdown preview
        # tool.
        filepath_browser = "file://{0}".format(filepath)
        webbrowser.open(filepath_browser)

    def create_filepath(file_dir, file_name):
        file_name = file_name if ".md" in file_name \
                else "{0}.md".format(file_name)
        return "{0}/{1}".format(file_dir, file_name)

    if args.action_name == 'new':
        created = datetime.utcnow().replace(microsecond=0)

        def create_stub_file(subdir_name, filename):
            dir_target = "{0}/{1}".format(js.root_directory, subdir_name)

            filepath = create_filepath(dir_target, filename)

            if os.path.isfile(filepath):
                raise IOError("File already exists! {0}".format(filepath))

            with open(filepath, 'w') as f:
                f.write("Author: {0}\n".format(js.author))
                f.write("Created: {0}\n".format(created.isoformat()))
                f.write("Version: {0}\n".format(js.document_version))
                f.write("Tags: \n")

            return filepath

        if args.element_type == 'log':
            # datetime.fromtimestamp(0) is not Unix epoch and returns
            # 1969-12-31 19:00 instead.
            epoch = datetime(1970, 1, 1)

            filepath = create_stub_file('LogEntries',
                str(int((created - epoch).total_seconds())))
        elif args.element_type == 'tag':
            filepath = create_stub_file('Tags', args.tag_name)

            # Add the title which should be the tag name
            with open(filepath, 'a') as f:
                # TODO: Would be very cool to reinforce camel case for the file
                # name and canonical for title.
                f.write("\n# {0}\n".format(args.tag_name))
        else:
            raise NotImplementedError("Unknown information type: {0}"
                    .format(args.element_type))

        if filepath:
            open_file_in_editor(filepath)
            show_file(filepath)
            print("Created: {0}, {1}".format(args.element_type, filepath))
        else:
            print("Failed to create new information element")
    elif args.action_name == 'edit':

        if args.element_type == 'log':
            filepath = create_filepath(js.logs_directory, args.log_entry_name)
        elif args.element_type == 'tag':
            filepath = create_filepath(js.tags_directory, args.tag_name)
        else:
            raise NotImplementedError("Unknown information type: {0}"
                    .format(args.element_type))

        edit_file(filepath)
        show_file(filepath)
        print("Editted: {0}, {1}".format(args.element_type, filepath))

    elif args.action_name == 'show':

        def convert_json_to_summary(src_json):
            """
            Form a summary representation of the log file.
            """
            # Clip the body
            clip = src_json['body'].split('\n')[0][0:250]
            return "\n".join([log_file, ", ".join(src_json['tags']), clip])

        if args.show_type == 'tags':
            tag_pattern = re.compile('(\w*)\.md')

            for tag_file in sorted(os.listdir(js.tags_directory)):
                tag = tag_pattern.search(tag_file).group(1)
                print(tag)
        elif args.show_type == 'tag':
            show_file(create_filepath(js.tags_directory, args.tag_name))
        elif args.show_type == 'logs':
            entries = []

            # 1. Go through each log file
            # 2. Convert each file to json
            # 3. Filter by tag if need be
            # 4. Print entries

            # NOTE: The sort order is increasing in time because the most recent
            # should be visible at the new command prompt.
            for log_file in sorted(os.listdir(js.logs_directory), reverse=False):
                log_path = "{0}/{1}".format(js.logs_directory, log_file)

                with open(log_path, 'r') as f:
                    json_rep = convert_file_to_json(f.read())

                if not args.tag or any([args.tag.lower() in tag.lower()
                    for tag in json_rep['tags']]):
                    entries.append(convert_json_to_summary(json_rep))

            if entries:
                print("\n\n".join(entries))
                print("\n\nLog entries found: {0}".format(len(entries)))
            else:
                print("No log entries found")
        elif args.show_type == 'lastlog':
            is_found = False

            for log_file in sorted(os.listdir(js.logs_directory), reverse=True):
                log_path = create_filepath(js.logs_directory, log_file)

                if args.tag:
                    with open(log_path, 'r') as f:
                        json_rep = convert_file_to_json(f.read())

                    if any([args.tag.lower() in tag.lower()
                        for tag in json_rep['tags']]):
                        show_file(log_path)
                        is_found = True
                        break
                else:
                    show_file(log_path)
                    is_found = True
                    break

            if not is_found:
                print("There is no log entry for \"{0}\"".format(args.tag))
        elif args.show_type == 'log':
            show_file(create_filepath(js.logs_directory, args.log_entry_name))
        else:
            raise NotImplementedError("Unknown show type: {0}"
                    .format(args.show_type))
