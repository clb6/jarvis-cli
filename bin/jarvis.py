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

    @property
    def author(self):
        return self._env_author

    @property
    def document_version(self):
        return self._env_version


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

    # Show actions
    parser_show = subparsers.add_parser('show', help='Show information elements')
    subparsers_show = parser_show.add_subparsers(help='Types of show actions',
            dest='show_type')

    parser_show_logs = subparsers_show.add_parser('logs', help='List all logs')
    parser_show_logs.add_argument('-t', '--tag', nargs='?', help='Tag to search')

    parser_show_tags = subparsers_show.add_parser('tags', help='List all tags')

    parser_show_tag = subparsers_show.add_parser('tag', help='Open a tag in the browser')
    parser_show_tag.add_argument('tag_name', help='Tag name')

    args = parser.parse_args()

    # NOTE: Argparse should filter and validate and ensure that only the known
    # choices get through to this point.
    # UPDATE: There is a case where the subsubparser allows for Nones to slip
    # through. The required flag doesn't seem to be reinforced so the following
    # is acceptable to Argparse which sucks for me:
    #   jarvis.py new

    js = JarvisSettings()

    if args.action_name == 'new':
        created = datetime.utcnow().replace(microsecond=0)

        def create_stub_file(subdir_name, filename):
            dir_target = "{0}/{1}".format(js.root_directory, subdir_name)

            filepath = "{0}/{1}.md".format(dir_target, filename)

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
                int((created - epoch).total_seconds()))
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
            subprocess.call(["vim", filepath])
            print("Created: {0}, {1}".format(args.element_type, filepath))
        else:
            print("Failed to create new information element")
    elif args.action_name == 'show':

        tags_dir = "{0}/{1}".format(js.root_directory, 'Tags')
        logs_dir = "{0}/{1}".format(js.root_directory, 'LogEntries')

        if args.show_type == 'tags':
            tag_pattern = re.compile('(\w*)\.md')

            for tag_file in sorted(os.listdir(tags_dir)):
                tag = tag_pattern.search(tag_file).group(1)
                print(tag)
        elif args.show_type == 'tag':
            filepath = "{0}/{1}.md".format(tags_dir, args.tag_name)

            if not os.path.isfile(filepath):
                raise IOError("Tag does not exist! {0}".format(filepath))

            # Previews the markdown. This will require you to change the
            # mimeapps.list setting file in order to chose your markdown preview
            # tool.
            filepath_browser = "file://{0}".format(filepath)
            webbrowser.open(filepath_browser)
        elif args.show_type == 'logs':
            def convert_file_to_json(src_file):
                """
                Form a json representation of a log file.
                """
                d = src_file.read().split('\n')

                def parse_metadata(line):
                    """
                    Looking for Author, Created, Version, Tags

                    :param line: line for metadata e.g. "Author: John Doe"
                    :type line: string

                    :return: (key string, value string)
                    """
                    m = re.search('^(Author|Created|Version|Tags): (.*)', line)
                    return m.group(1).lower(), m.group(2)

                t = (parse_metadata(d[i]) for i in range(0, 4))
                response = dict(t)
                response['tags'] = response['tags'].split(', ')
                response['body'] = "\n".join(d[5:])
                return response

            def convert_json_to_summary(src_json):
                """
                Form a summary representation of the log file.
                """
                # Clip the body
                clip = src_json['body'].split('\n')[0][0:250]
                return "\n".join([log_file, ", ".join(src_json['tags']), clip])

            entries = []

            # 1. Go through each log file
            # 2. Convert each file to json
            # 3. Filter by tag if need be
            # 4. Print entries
            for log_file in sorted(os.listdir(logs_dir), reverse=True):
                log_path = "{0}/{1}".format(logs_dir, log_file)

                with open(log_path, 'r') as f:
                    json_rep = convert_file_to_json(f)

                if not args.tag or any([args.tag.lower() in tag.lower()
                    for tag in json_rep['tags']]):
                    entries.append(convert_json_to_summary(json_rep))

            if entries:
                print("\n\n".join(entries))
                print("\n\nLog entries found: {0}".format(len(entries)))
            else:
                print("No log entries found")
        else:
            raise NotImplementedError("Unknown show type: {0}"
                    .format(args.show_type))
